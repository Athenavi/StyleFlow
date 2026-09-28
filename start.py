#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""StyleFlow 一键启动器（本地 / 局域网，零配置）

面向"只想把项目跑起来"的使用者：不需要手工安装 PostgreSQL、Redis、MinIO，
也不需要自己创建虚拟环境。脚本会自动完成：

  1. 找到/创建 Python 虚拟环境并安装后端依赖
  2. 生成并维护根目录 .env（随机密钥、SQLite、同源部署设置）
  3. 安装前端依赖、按需构建前端
  4. 初始化数据库（默认 SQLite）、准备管理员账号
  5. 启动后端 + 前端，打印本机与局域网访问地址

常用命令：
    python start.py                  # 启动（同一局域网内其他设备可访问）
    python start.py --check          # 只做环境自检，不启动
    python start.py --port 8080      # 更换前端端口
    python start.py --local          # 仅本机可访问（不监听局域网）
    python start.py --dev            # 前端开发模式（不构建，改代码即时生效）
    python start.py --rebuild        # 强制重新安装/构建前端
    python start.py --db postgres    # 使用 .env 中的 PostgreSQL 配置
    python start.py --reset-admin    # 重置管理员密码并打印
    python start.py --stop           # 停止已启动的服务

按 Ctrl+C 停止全部服务。日志见 data/logs/。
"""
from __future__ import annotations

import argparse
import json
import os
import re
import secrets
import shutil
import signal
import socket
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BACKEND = ROOT / 'backend'
FRONTEND = ROOT / 'frontend'
ENV_FILE = ROOT / '.env'
FRONTEND_ENV = FRONTEND / '.env.local'
REQUIREMENTS = BACKEND / 'requirements' / 'local.txt'

IS_WIN = os.name == 'nt'
VENV_PY = ('Scripts', 'python.exe') if IS_WIN else ('bin', 'python')
DEFAULT_BACKEND_PORT = 8000
DEFAULT_FRONTEND_PORT = 3000

# 后端所需的关键第三方模块（缺失则自动安装依赖）
REQUIRED_MODULES = [
    'django', 'ninja', 'corsheaders', 'django_filters',
    'jwt', 'cryptography', 'requests', 'dotenv',
    'openai', 'anthropic', 'celery',
]

_procs: list[tuple[str, subprocess.Popen]] = []


# --------------------------------------------------------------------------- #
# 终端输出
# --------------------------------------------------------------------------- #
def _setup_console() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            # 行缓冲：被重定向到日志/管道时也能实时看到进度
            stream.reconfigure(encoding='utf-8', errors='replace', line_buffering=True)  # type: ignore[attr-defined]
        except Exception:
            pass
    if IS_WIN:
        try:  # 启用 ANSI 颜色
            import ctypes
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
        except Exception:
            pass


# 尽早切换到 UTF-8 输出，避免 Windows 控制台（GBK）打印符号/中文时报错
_setup_console()


def _c(text: str, code: str) -> str:
    return f'\033[{code}m{text}\033[0m'


def step(text: str) -> None:
    print(f'\n{_c("▶", "36")} {_c(text, "1")}')


def info(text: str) -> None:
    print(f'  {text}')


def ok(text: str) -> None:
    print(f'  {_c("✓", "32")} {text}')


def warn(text: str) -> None:
    print(f'  {_c("!", "33")} {text}')


def fail(text: str) -> None:
    print(f'  {_c("×", "31")} {text}')


def die(text: str, hint: str = '') -> None:
    fail(text)
    if hint:
        print(f'    {hint}')
    sys.exit(1)


# --------------------------------------------------------------------------- #
# .env 读写
# --------------------------------------------------------------------------- #
def read_env(path: Path = ENV_FILE) -> dict:
    data: dict[str, str] = {}
    if not path.exists():
        return data
    for line in path.read_text(encoding='utf-8', errors='ignore').splitlines():
        s = line.strip()
        if not s or s.startswith('#') or '=' not in s:
            continue
        key, value = s.split('=', 1)
        data[key.strip()] = value.strip()
    return data


def merge_env(path: Path, updates: dict) -> bool:
    """原地更新 .env：已存在的键改写、缺失的键追加；内容有变化时先备份"""
    old_lines = path.read_text(encoding='utf-8').splitlines() if path.exists() else []
    remaining = {k: str(v) for k, v in updates.items()}
    new_lines: list[str] = []
    for line in old_lines:
        m = re.match(r'\s*([A-Za-z_][A-Za-z0-9_]*)\s*=', line)
        if m and m.group(1) in remaining:
            new_lines.append(f'{m.group(1)}={remaining.pop(m.group(1))}')
        else:
            new_lines.append(line)
    if remaining:
        if new_lines and new_lines[-1].strip():
            new_lines.append('')
        new_lines.append('# ---- 由 start.py 自动维护 ----')
        new_lines.extend(f'{k}={v}' for k, v in remaining.items())

    new_text = '\n'.join(new_lines).rstrip('\n') + '\n'
    old_text = ('\n'.join(old_lines).rstrip('\n') + '\n') if old_lines else ''
    if new_text == old_text:
        return False
    if path.exists():
        backup = path.with_name(f'{path.name}.bak.{time.strftime("%Y%m%d-%H%M%S")}')
        shutil.copy2(path, backup)
        info(f'已备份原配置: {backup.name}')
    path.write_text(new_text, encoding='utf-8')
    return True


def ensure_env(backend_port: int, frontend_port: int, db_mode: str | None) -> dict:
    """生成/纠正 .env 中由脚本托管的配置项，返回生效后的配置"""
    env = read_env()
    updates: dict[str, str] = {}

    if not env.get('DJANGO_SECRET_KEY') or env['DJANGO_SECRET_KEY'].startswith('change-me'):
        updates['DJANGO_SECRET_KEY'] = secrets.token_urlsafe(48)
    if not env.get('API_KEY_ENCRYPTION_KEY'):
        updates['API_KEY_ENCRYPTION_KEY'] = secrets.token_urlsafe(32)

    updates['DJANGO_SETTINGS_MODULE'] = 'config.settings.local'
    updates['DJANGO_DEBUG'] = env.get('DJANGO_DEBUG') or 'true'
    updates['DATABASE_MODE'] = (db_mode or env.get('DATABASE_MODE') or 'sqlite').lower()
    updates['TASK_BACKEND'] = env.get('TASK_BACKEND') or 'thread'
    updates['STORAGE_BACKEND'] = env.get('STORAGE_BACKEND') or 'local'
    # 前后端同源部署：必须留空，否则局域网/域名访问时图片 URL 会指向访客自己的 localhost
    updates['BACKEND_BASE_URL'] = ''
    updates['BACKEND_PORT'] = str(backend_port)
    updates['FRONTEND_PORT'] = str(frontend_port)
    updates['STYLEFLOW_ADMIN_USER'] = env.get('STYLEFLOW_ADMIN_USER') or 'admin'
    if not env.get('STYLEFLOW_ADMIN_PASSWORD'):
        updates['STYLEFLOW_ADMIN_PASSWORD'] = secrets.token_urlsafe(9)

    if merge_env(ENV_FILE, updates):
        ok('已更新运行配置 .env')
    else:
        ok('运行配置 .env 已是最新')
    return read_env()


# --------------------------------------------------------------------------- #
# 环境探测
# --------------------------------------------------------------------------- #
def find_python() -> Path:
    for venv in (BACKEND / '.venv', ROOT / '.venv'):
        exe = venv.joinpath(*VENV_PY)
        if exe.exists():
            return exe
    return Path(sys.executable)


def python_version(py: Path) -> tuple[int, int, int] | None:
    try:
        r = subprocess.run([str(py), '-c', 'import sys;print("%d.%d.%d" % sys.version_info[:3])'],
                           capture_output=True, text=True, timeout=30)
        if r.returncode != 0:
            return None
        return tuple(int(x) for x in r.stdout.strip().split('.'))  # type: ignore[return-value]
    except Exception:
        return None


def missing_modules(py: Path, modules: list[str]) -> list[str]:
    code = ('import importlib.util as u, json, sys;'
            'print(json.dumps([m for m in sys.argv[1:] if u.find_spec(m) is None]))')
    try:
        r = subprocess.run([str(py), '-c', code, *modules], capture_output=True, text=True, timeout=60)
        if r.returncode == 0 and r.stdout.strip():
            return json.loads(r.stdout.strip())
    except Exception:
        pass
    return []


def run(cmd: list, cwd: Path | None = None, env: dict | None = None, check: bool = True) -> int:
    full_env = os.environ.copy()
    if env:
        full_env.update(env)
    printable = ' '.join(str(c) for c in cmd)
    print(f'    $ {printable}')
    r = subprocess.run([str(c) for c in cmd], cwd=str(cwd) if cwd else None, env=full_env)
    if check and r.returncode != 0:
        die(f'命令执行失败（退出码 {r.returncode}）', printable)
    return r.returncode


def ensure_python_env(py: Path, db_mode: str, do_install: bool = True) -> Path:
    """返回可用的 Python 解释器；缺失依赖时安装"""
    version = python_version(py)
    if version is None:
        die(f'无法执行 Python: {py}', '请安装 Python 3.12 或更高版本后重试')
    if version < (3, 12):
        die(f'Python 版本过低: {version[0]}.{version[1]}.{version[2]}',
            'Django 6 需要 Python 3.12+，请升级后重试')

    has_venv = '.venv' in str(py) or 'venv' in str(py)
    if not has_venv:
        target = BACKEND / '.venv'
        exe = target.joinpath(*VENV_PY)
        if not exe.exists() and do_install:
            info('未发现虚拟环境，正在创建 backend/.venv ...')
            run([py, '-m', 'venv', str(target)])
        if exe.exists():
            py = exe

    modules = list(REQUIRED_MODULES)
    if db_mode == 'postgres':
        modules.append('psycopg2')
    missing = missing_modules(py, modules)
    if missing:
        if not do_install:
            die(f'缺少依赖: {", ".join(missing)}', '请重新运行不带 --check 的命令以自动安装')
        info(f'缺少依赖: {", ".join(missing)}，正在安装（首次约 1-3 分钟）...')
        run([py, '-m', 'pip', 'install', '-r', str(REQUIREMENTS)])
        missing = missing_modules(py, modules)
        if missing:
            die(f'依赖安装后仍缺失: {", ".join(missing)}', f'可手工执行: {py} -m pip install -r {REQUIREMENTS}')
    ok(f'Python 环境就绪 ({py})')
    return py


def ensure_node(do_install: bool = True) -> tuple[Path, Path]:
    node = shutil.which('node')
    npm = shutil.which('npm')
    if not node or not npm:
        die('未检测到 Node.js', '请安装 Node.js 20 或更高版本：https://nodejs.org/  （Windows 可用: winget install OpenJS.NodeJS.LTS）')
    try:
        r = subprocess.run([node, '-v'], capture_output=True, text=True, timeout=30)
        major = int(re.sub(r'[^0-9]', '', r.stdout.strip() or '0')[:2] or 0)
    except Exception:
        major = 0
    if major and major < 20:
        die(f'Node.js 版本过低: {r.stdout.strip()}', 'StyleFlow 前端需要 Node.js 20+')
    ok(f'Node.js 就绪 ({node})')
    return Path(node), Path(npm)


def npm_install(npm: Path) -> None:
    """安装前端依赖：优先 `npm ci`（快、可复现），失败时自动回退 `npm install`"""
    info('正在安装前端依赖（首次约 2-5 分钟，请耐心等待）...')
    lock = FRONTEND / 'package-lock.json'
    if lock.exists():
        code = run([npm, 'ci', '--no-audit', '--no-fund'], cwd=FRONTEND, check=False)
        if code == 0:
            return
        warn('npm ci 失败（通常是 package-lock.json 与 package.json 不同步），改用 npm install 重试 ...')
    run([npm, 'install', '--no-audit', '--no-fund'], cwd=FRONTEND)


def frontend_signature(backend_origin: str, dev: bool) -> dict:
    def mtime(path: Path) -> float:
        try:
            return round(path.stat().st_mtime, 3)
        except OSError:
            return 0.0

    src_latest = 0.0
    src_dir = FRONTEND / 'src'
    if src_dir.exists():
        for p in src_dir.rglob('*'):
            if p.is_file():
                src_latest = max(src_latest, p.stat().st_mtime)
    return {
        'backend_origin': backend_origin,
        'mode': 'dev' if dev else 'prod',
        'src_mtime': round(src_latest, 3),
        'config': {name: mtime(FRONTEND / name) for name in
                   ('next.config.ts', 'package.json', 'package-lock.json', 'tsconfig.json')},
    }


# --------------------------------------------------------------------------- #
# Django 管理命令
# --------------------------------------------------------------------------- #
def manage(py: Path, args: list, env_vars: dict, quiet: bool = False) -> int:
    cmd = [py, 'manage.py', *args]
    if quiet:
        full_env = os.environ.copy()
        full_env.update(env_vars)
        r = subprocess.run([str(c) for c in cmd], cwd=str(BACKEND), env=full_env,
                           capture_output=True, text=True, errors='replace')
        if r.returncode != 0:
            print(r.stdout[-4000:])
            print(r.stderr[-4000:])
            die(f'manage.py {" ".join(args)} 执行失败')
        return r.returncode
    return run(cmd, cwd=BACKEND, env=env_vars)


def migrate_legacy_media(data_dir: Path) -> None:
    """一次性兼容：把历史版本上传目录挪到新的 data/media"""
    target = data_dir / 'media'
    try:
        if target.exists() and any(target.rglob('*')):
            return
    except OSError:
        return
    for legacy in (BACKEND / 'config' / 'media', BACKEND / 'media'):
        if legacy.exists() and any(p.is_file() for p in legacy.rglob('*')):
            shutil.copytree(legacy, target, dirs_exist_ok=True)
            ok(f'已迁移历史媒体文件: {legacy} → {target}')
            return


def prepare_sqlite(data_dir: Path, env: dict) -> None:
    """为 SQLite 开启 WAL 模式，提升多线程读写并发表现"""
    import sqlite3
    db_path = Path(env.get('SQLITE_PATH') or (data_dir / 'styleflow.sqlite3'))
    if not db_path.is_absolute():
        db_path = ROOT / db_path
    try:
        con = sqlite3.connect(str(db_path))
        con.execute('PRAGMA journal_mode=WAL;')
        con.execute('PRAGMA synchronous=NORMAL;')
        con.commit()
        con.close()
    except Exception as exc:
        warn(f'SQLite 优化设置失败（不影响使用）: {exc}')


ADMIN_CODE = (
    'from django.contrib.auth.models import User\n'
    'from apps.accounts.models import Profile\n'
    'import os\n'
    'username = os.environ["STYLEFLOW_ADMIN_USER"]\n'
    'password = os.environ["STYLEFLOW_ADMIN_PASSWORD"]\n'
    'reset = os.environ.get("STYLEFLOW_ADMIN_RESET") == "1"\n'
    'user = User.objects.filter(username=username).first()\n'
    'created = user is None\n'
    'if created:\n'
    '    user = User.objects.create_user(username, password=password)\n'
    'if reset:\n'
    '    user.set_password(password)\n'
    'user.is_staff = True\n'
    'user.is_superuser = True\n'
    'user.is_active = True\n'
    'user.save()\n'
    'profile, _ = Profile.objects.get_or_create(user=user)\n'
    'profile.role = "admin"\n'
    'profile.save()\n'
    'print("START_ADMIN_RESULT:", "created" if created else "exists")\n'
)


def ensure_admin_account(py: Path, env: dict, data_dir: Path, reset: bool = False) -> bool:
    env_vars = {
        'DJANGO_SETTINGS_MODULE': 'config.settings.local',
        'STYLEFLOW_ADMIN_USER': env.get('STYLEFLOW_ADMIN_USER', 'admin'),
        'STYLEFLOW_ADMIN_PASSWORD': env.get('STYLEFLOW_ADMIN_PASSWORD', ''),
        'STYLEFLOW_ADMIN_RESET': '1' if reset else '0',
    }
    full_env = os.environ.copy()
    full_env.update(env_vars)
    r = subprocess.run([str(py), 'manage.py', 'shell', '-c', ADMIN_CODE], cwd=str(BACKEND),
                       env=full_env, capture_output=True, text=True, errors='replace')
    if r.returncode != 0:
        warn('管理员账号初始化失败')
        print((r.stdout + r.stderr)[-2000:])
        return False
    created = 'created' in r.stdout
    if created or reset:
        account_file = data_dir / '管理员账号.txt'
        account_file.parent.mkdir(parents=True, exist_ok=True)
        account_file.write_text(
            f'用户名: {env_vars["STYLEFLOW_ADMIN_USER"]}\n'
            f'密码:   {env_vars["STYLEFLOW_ADMIN_PASSWORD"]}\n'
            f'登录地址: http://127.0.0.1:{env.get("FRONTEND_PORT", DEFAULT_FRONTEND_PORT)}/login\n'
            '（登录后可在界面右上角修改密码；此文件可删除）\n',
            encoding='utf-8')
        ok(f'管理员账号已写入 data/{account_file.name}')
    return True


# --------------------------------------------------------------------------- #
# 进程管理
# --------------------------------------------------------------------------- #
def _pump(proc: subprocess.Popen, name: str, log_handle, prefix_color: str) -> None:
    if proc.stdout is None:
        return
    for line in proc.stdout:
        log_handle.write(line)
        sys.stdout.write(f'{_c("[" + name + "]", prefix_color)} {line.rstrip()}\n')
        sys.stdout.flush()


def spawn(name: str, cmd: list, cwd: Path, env_vars: dict, log_path: Path, color: str) -> subprocess.Popen:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_handle = open(log_path, 'a', encoding='utf-8', errors='replace')
    log_handle.write(f'\n===== {time.strftime("%Y-%m-%d %H:%M:%S")} 启动 {name}: '
                     f'{" ".join(str(c) for c in cmd)} =====\n')
    log_handle.flush()

    kwargs: dict = dict(
        cwd=str(cwd), stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, encoding='utf-8', errors='replace', bufsize=1,
    )
    if IS_WIN:
        kwargs['creationflags'] = subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        kwargs['start_new_session'] = True

    full_env = os.environ.copy()
    full_env.update(env_vars)
    try:
        proc = subprocess.Popen([str(c) for c in cmd], env=full_env, **kwargs)
    except OSError as exc:
        die(f'{name} 启动失败: {exc}')
        raise
    threading.Thread(target=_pump, args=(proc, name, log_handle, color), daemon=True).start()
    _procs.append((name, proc))
    return proc


def stop_all() -> None:
    for name, proc in _procs:
        if proc.poll() is not None:
            continue
        info(f'正在停止 {name} ...')
        try:
            if IS_WIN:
                subprocess.run(['taskkill', '/F', '/T', '/PID', str(proc.pid)],
                               capture_output=True, text=True)
            else:
                os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        except Exception:
            try:
                proc.terminate()
            except Exception:
                pass
    deadline = time.time() + 15
    for _, proc in _procs:
        while proc.poll() is None and time.time() < deadline:
            time.sleep(0.2)


def pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    if IS_WIN:
        r = subprocess.run(['tasklist', '/FI', f'PID eq {pid}'], capture_output=True, text=True, errors='replace')
        return str(pid) in (r.stdout or '')
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def stop_by_pidfile(data_dir: Path) -> None:
    pid_file = data_dir / 'run' / 'pids.json'
    if not pid_file.exists():
        info('没有找到运行中的实例')
        return
    try:
        pids = json.loads(pid_file.read_text(encoding='utf-8'))
    except Exception:
        pids = {}
    for name, pid in pids.items():
        if pid_alive(int(pid)):
            info(f'停止 {name} (PID {pid}) ...')
            if IS_WIN:
                subprocess.run(['taskkill', '/F', '/T', '/PID', str(pid)], capture_output=True, text=True)
            else:
                try:
                    os.kill(int(pid), signal.SIGTERM)
                except OSError:
                    pass
        else:
            info(f'{name} (PID {pid}) 已不在运行')
    pid_file.unlink(missing_ok=True)
    ok('已停止')


def write_pids(data_dir: Path) -> None:
    run_dir = data_dir / 'run'
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / 'pids.json').write_text(
        json.dumps({name: proc.pid for name, proc in _procs}, indent=2), encoding='utf-8')


# --------------------------------------------------------------------------- #
# 端口 / 网络
# --------------------------------------------------------------------------- #
def port_in_use(port: int, host: str = '127.0.0.1') -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.6)
        return s.connect_ex((host, port)) == 0


def lan_ips() -> tuple[str | None, list[str]]:
    """返回 (默认出口网卡地址, 其它网卡地址列表)；虚拟网卡排在后面"""
    primary = None
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        primary = s.getsockname()[0]
        s.close()
    except Exception:
        pass

    others: set[str] = set()
    try:
        for info_ in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            others.add(info_[4][0])
    except Exception:
        pass

    others.discard(primary)
    ordered = [ip for ip in others if not ip.startswith(('127.', '169.254.'))]
    # 以 .1 结尾的多为虚拟网卡/网关（WSL、VMware、Docker），排到最后
    ordered.sort(key=lambda ip: ip.endswith('.1'))
    return primary, ordered[:3]


def http_ready(url: str, timeout: float = 2.0) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return 200 <= resp.status < 500
    except urllib.error.HTTPError:
        return True          # 有 HTTP 响应即说明服务已就绪
    except Exception:
        return False


def wait_ready(name: str, url: str, timeout: int, proc: subprocess.Popen | None = None) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if http_ready(url):
            ok(f'{name} 已就绪')
            return True
        if proc is not None and proc.poll() is not None:
            fail(f'{name} 进程已退出（退出码 {proc.returncode}）')
            return False
        time.sleep(1)
    fail(f'{name} 在 {timeout}s 内未就绪: {url}')
    return False


# --------------------------------------------------------------------------- #
# 主流程
# --------------------------------------------------------------------------- #
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='StyleFlow 一键启动器（本地 / 局域网）',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument('--check', action='store_true', help='只做环境自检，不启动服务')
    parser.add_argument('--port', type=int, default=None, help=f'前端端口（默认 {DEFAULT_FRONTEND_PORT}）')
    parser.add_argument('--backend-port', type=int, default=None, help=f'后端端口（默认 {DEFAULT_BACKEND_PORT}）')
    parser.add_argument('--host', default=None, help='监听地址（默认 0.0.0.0）')
    parser.add_argument('--local', action='store_true', help='仅允许本机访问（等价于 --host 127.0.0.1）')
    parser.add_argument('--dev', action='store_true', help='前端使用开发模式（不构建）')
    parser.add_argument('--rebuild', action='store_true', help='强制重新安装依赖并构建前端')
    parser.add_argument('--db', choices=['sqlite', 'postgres'], default=None, help='数据库类型（默认 sqlite）')
    parser.add_argument('--reset-admin', action='store_true', help='重置管理员密码')
    parser.add_argument('--stop', action='store_true', help='停止已启动的服务')
    parser.add_argument('--no-browser', action='store_true', help='启动后不自动打开浏览器')
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    print(_c('\n  StyleFlow · 本地一键启动器', '1'))
    print('  AI 驱动的服装设计-生产协同平台\n')

    current_env = read_env()
    data_dir = Path(current_env.get('STYLEFLOW_DATA_DIR') or (ROOT / 'data'))
    if not data_dir.is_absolute():
        data_dir = ROOT / data_dir

    if args.stop:
        step('停止服务')
        stop_by_pidfile(data_dir)
        return

    backend_port = args.backend_port or int(current_env.get('BACKEND_PORT') or DEFAULT_BACKEND_PORT)
    frontend_port = args.port or int(current_env.get('FRONTEND_PORT') or DEFAULT_FRONTEND_PORT)
    host = '127.0.0.1' if args.local else (args.host or '0.0.0.0')

    # ---------- 1. 环境自检 ----------
    step('检查运行环境')
    py = ensure_python_env(find_python(), args.db or current_env.get('DATABASE_MODE') or 'sqlite',
                           do_install=not args.check)
    ensure_node()

    if args.check:
        env = current_env
        step('自检结果')
        ok(f'项目根目录: {ROOT}')
        ok(f'数据目录:   {data_dir}')
        ok(f'前端端口:   {frontend_port}（后端 {backend_port}）')
        ok(f'数据库模式: {(args.db or env.get("DATABASE_MODE") or "sqlite")}')
        if not ENV_FILE.exists():
            warn('.env 尚未生成，首次启动时会自动创建')
        if not (FRONTEND / 'node_modules').exists():
            warn('前端依赖尚未安装（首次启动会自动执行 npm ci）')
        if not (FRONTEND / '.next').exists() and not args.dev:
            warn('前端尚未构建（首次启动会自动构建，约 3-10 分钟）')
        if port_in_use(frontend_port) or port_in_use(backend_port):
            warn(f'端口 {frontend_port}/{backend_port} 已被占用，请确认没有重复启动')
        print('\n  自检完成。执行 `python start.py` 即可启动。\n')
        return

    # ---------- 2. 配置 ----------
    step('准备运行配置')
    env = ensure_env(backend_port, frontend_port, args.db)
    if args.reset_admin:
        env['STYLEFLOW_ADMIN_PASSWORD'] = secrets.token_urlsafe(9)
        merge_env(ENV_FILE, {'STYLEFLOW_ADMIN_PASSWORD': env['STYLEFLOW_ADMIN_PASSWORD']})
        info('已生成新的管理员密码，稍后会显示')
    db_mode = (env.get('DATABASE_MODE') or 'sqlite').lower()
    if db_mode == 'postgres':
        info('数据库模式: postgres（使用 .env 中的 DB_* 配置）')
    else:
        info('数据库模式: sqlite（零配置，无需安装数据库）')

    # 依赖可能因数据库模式变化而需要补充（如切换 postgres）
    py = ensure_python_env(py, db_mode)

    for port, label in ((backend_port, '后端'), (frontend_port, '前端')):
        if port_in_use(port):
            if (data_dir / 'run' / 'pids.json').exists():
                die(f'{label}端口 {port} 已被占用，看起来 StyleFlow 已经在运行',
                    f'如需重启请先执行: python start.py --stop')
            die(f'{label}端口 {port} 已被其它程序占用', '可用 --port / --backend-port 指定其它端口')

    # ---------- 3. 前端依赖与构建 ----------
    step('准备前端')
    node, npm = ensure_node()
    if args.rebuild and (FRONTEND / 'node_modules').exists():
        info('--rebuild：重新安装前端依赖')
        shutil.rmtree(FRONTEND / 'node_modules', ignore_errors=True)
    if not (FRONTEND / 'node_modules').exists():
        npm_install(npm)

    next_bin = FRONTEND / 'node_modules' / 'next' / 'dist' / 'bin' / 'next'
    if not next_bin.exists():
        npm_install(npm)
    if not next_bin.exists():
        die('前端依赖不完整（缺少 next 命令）', f'请手工执行: cd {FRONTEND} && npm install')

    backend_origin = f'http://127.0.0.1:{backend_port}'
    # 前端构建/运行所需配置（同源 API 代理）
    merge_env(FRONTEND_ENV, {
        'NEXT_PUBLIC_API_URL': '/api/v1',
        'STYLEFLOW_BACKEND_ORIGIN': backend_origin,
    })

    build_stamp = data_dir / 'run' / 'frontend-build.json'
    signature = frontend_signature(backend_origin, args.dev)
    need_build = args.dev is False and (
        args.rebuild
        or not (FRONTEND / '.next' / 'BUILD_ID').exists()
        or not build_stamp.exists()
        or json.loads(build_stamp.read_text(encoding='utf-8')) != signature
    )
    if need_build:
        print()
        warn('首次构建或代码有更新，正在构建前端（约 3-10 分钟，请勿关闭窗口）...')
        run([node, next_bin, 'build'], cwd=FRONTEND,
            env={'NEXT_PUBLIC_API_URL': '/api/v1', 'STYLEFLOW_BACKEND_ORIGIN': backend_origin})
        build_stamp.parent.mkdir(parents=True, exist_ok=True)
        build_stamp.write_text(json.dumps(signature, indent=2), encoding='utf-8')
        ok('前端构建完成')
    else:
        ok('前端构建产物已是最新')

    # ---------- 4. 数据库 ----------
    step('准备数据库')
    data_dir.mkdir(parents=True, exist_ok=True)
    migrate_legacy_media(data_dir)
    django_env = {'DJANGO_SETTINGS_MODULE': 'config.settings.local'}
    if db_mode == 'sqlite':
        prepare_sqlite(data_dir, env)
    manage(py, ['migrate', '--noinput'], django_env, quiet=True)
    ok('数据库结构已就绪')
    if not (data_dir / 'static' / 'admin').exists() or args.rebuild:
        manage(py, ['collectstatic', '--noinput'], django_env, quiet=True)
        ok('后台静态资源已收集')
    ensure_admin_account(py, env, data_dir, reset=args.reset_admin)

    # ---------- 5. 启动服务 ----------
    step('启动服务')
    logs_dir = data_dir / 'logs'
    has_waitress = 'waitress' not in missing_modules(py, ['waitress'])
    if has_waitress:
        backend_cmd = [py, '-m', 'waitress', f'--host={host}', f'--port={backend_port}',
                       '--threads=8', '--ident=StyleFlow', 'config.wsgi:application']
    else:
        backend_cmd = [py, 'manage.py', 'runserver', f'{host}:{backend_port}', '--noreload']

    backend_proc = spawn('backend', backend_cmd, BACKEND, django_env,
                         logs_dir / 'backend.log', '35')

    if args.dev:
        frontend_cmd = [node, next_bin, 'dev', '-H', host, '-p', str(frontend_port)]
    else:
        frontend_cmd = [node, next_bin, 'start', '-H', host, '-p', str(frontend_port)]
    frontend_proc = spawn('frontend', frontend_cmd, FRONTEND,
                          {'NEXT_PUBLIC_API_URL': '/api/v1', 'STYLEFLOW_BACKEND_ORIGIN': backend_origin},
                          logs_dir / 'frontend.log', '36')

    write_pids(data_dir)

    step('等待服务就绪')
    backend_ok = wait_ready('后端 API', f'http://127.0.0.1:{backend_port}/api/v1/docs', 120, backend_proc)
    frontend_ok = wait_ready('前端页面', f'http://127.0.0.1:{frontend_port}/', 120, frontend_proc)

    if not (backend_ok and frontend_ok):
        fail('启动失败，请查看日志（下方为末尾内容）')
        for log_name in ('backend.log', 'frontend.log'):
            log_file = logs_dir / log_name
            if log_file.exists():
                tail = log_file.read_text(encoding='utf-8', errors='replace').splitlines()[-25:]
                print(f'\n--- {log_name} ---')
                print('\n'.join(tail))
        stop_all()
        sys.exit(1)

    # ---------- 6. 访问信息 ----------
    local_url = f'http://127.0.0.1:{frontend_port}'
    primary_ip, other_ips = (None, []) if host == '127.0.0.1' else lan_ips()
    lan_url = primary_ip or (other_ips[0] if other_ips else '')
    admin_user = env.get('STYLEFLOW_ADMIN_USER', 'admin')
    admin_password = env.get('STYLEFLOW_ADMIN_PASSWORD', '')

    print()
    print(_c('  ✓ StyleFlow 已启动', '32'))
    print(f'    本机访问      {local_url}')
    if lan_url:
        print(f'    局域网访问    http://{lan_url}:{frontend_port}'
              f'   ← 同一 WiFi 下的手机/电脑可直接打开')
        extra = [ip for ip in other_ips if ip != lan_url]
        if extra:
            print(f'    其它网卡      ' + ', '.join(f'http://{ip}:{frontend_port}' for ip in extra))
    else:
        print('    （当前仅允许本机访问；去掉 --local 即可让局域网设备访问）')
    print(f'    接口文档      {local_url}/api/v1/docs')
    print(f'    管理后台      http://127.0.0.1:{backend_port}/admin/   (Django 管理后台，端口 {backend_port})')
    print(f'    默认账号      {admin_user} / {admin_password}')
    print(f'    数据目录      {data_dir}')
    print(f'    日志          {logs_dir}')
    print(f'    停止服务      Ctrl+C（或另开窗口执行 python start.py --stop）')
    if IS_WIN and lan_url:
        print('\n' + _c('  提示：', '33')
              + '若局域网设备打不开，请允许 Windows 防火墙放行（管理员 PowerShell 执行一次）：')
        print(f'      netsh advfirewall firewall add rule name="StyleFlow" '
              f'dir=in action=allow protocol=TCP localport={frontend_port}')
    print()

    if not args.no_browser:
        try:
            webbrowser.open(local_url)
        except Exception:
            pass

    try:
        while True:
            time.sleep(0.5)
            for name, proc in list(_procs):
                if proc.poll() is not None:
                    fail(f'{name} 进程意外退出（退出码 {proc.returncode}），正在关闭其它服务')
                    stop_all()
                    sys.exit(1)
    except KeyboardInterrupt:
        print()
        step('收到退出信号，正在关闭服务')
        stop_all()
        ok('已全部停止，再见 👋')


if __name__ == '__main__':
    main()
