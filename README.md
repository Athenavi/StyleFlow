<p align="center">
  <img src="https://img.shields.io/badge/license-MIT-blue" alt="License">
  <img src="https://img.shields.io/badge/python-3.12%2B-blue" alt="Python">
  <img src="https://img.shields.io/badge/django-6.0%2B-green" alt="Django">
  <img src="https://img.shields.io/badge/next.js-16-purple" alt="Next.js">
  <img src="https://img.shields.io/badge/PRs-welcome-brightgreen" alt="PRs Welcome">
</p>

<h1 align="center">🎨 StyleFlow</h1>
<p align="center"><b>AI 驱动的服装设计-生产协同平台</b></p>

<p align="center">
  <i>让灵感自然涌动，让流程自如流转。</i>
</p>

<p align="center">
  <a href="#-快速开始零配置">快速开始</a> •
  <a href="#-功能特性">功能特性</a> •
  <a href="#-技术栈">技术栈</a> •
  <a href="#-项目结构">项目结构</a> •
  <a href="docs/部署/01-本地一键运行.md">部署文档</a> •
  <a href="README_EN.md">English</a>
</p>

---

## ✨ 功能特性

### 🤖 AI 设计工坊
| 功能 | 说明 |
|------|------|
| **文生图** | 输入提示词，AI 生成服装设计稿（支持 5 种模板） |
| **图生图/款式延展** | 上传参考图，ControlNet 风格迁移 |
| **设计稿管理** | 个人作品库、分类管理、版本历史 |
| **多模型支持** | OpenAI / Claude / 通义千问 随时切换 |

### 👗 虚拟试衣
| 功能 | 说明 |
|------|------|
| **单人换装合成** | 人物图 + 服装图 → AI 合成试穿效果 |
| **媒体库集成** | 从媒体库选择素材，一键导入 |
| **示例图片** | 内置示例，快速体验 |
| **结果自动入库** | 试衣结果自动保存到媒体库 |

### 📋 工艺单管理
- AI 自动生成工艺单（LLM 提取工艺参数 + 匹配工序模板）
- 尺码表、工序列表、面料说明
- 审核流程

### 🔄 可视化工作流
- **可视化编辑器**：拖拽式节点编排，支持 10 条自定义工作流
- **角色权限**：认领机制（先到先得），handler_role 权限校验
- **自动推进**：auto_proceed 节点自动流转
- **内置模板**：款式开发 / 物料审批 / AI 辅助设计
- **待办看板**：可认领/处理/推进/驳回

### 📁 媒体库
- 支持 JPG / PNG / WebP / GIF，单文件 ≤10MB
- 6 种分类：模特图 / 服装图 / 面料图 / 设计稿 / 灵感图 / 其他
- 批量操作：批量分类、批量删除
- 回收站：文件级回收（移入 .trash 目录）
- 分页加载

### 📊 核工价 & 计件工资
- 工序模板匹配，自动核算工费
- 工资报表：按工号、日期筛选
- 统计看板：总人数 / 总金额 / 总件数

### 🔗 ERP 对接
- 数据库直连同步引擎
- 款式数据镜像 + 工序标准数据
- 回写机制

### 🛡️ 安全特性
| 特性 | 说明 |
|------|------|
| API Key 加密 | Fernet 双层加密（独立密钥 + 用户密码） |
| 密码变更 → Key 失效 | 用户改密后旧 Key 自动无法解密 |
| JWT 认证 | Access Token 30min + Refresh Token 7d |
| 角色权限 | 6 种角色，菜单级 + 接口级权限控制 |

---

## 🚀 快速开始（零配置）

> 不需要安装 PostgreSQL / Redis / MinIO，也不需要自己创建虚拟环境或配密码。
> 一键脚本会自动准备环境、初始化数据库、构建前端并启动服务。

### 前置要求（只需这两样）

- **Python 3.12+** → <https://www.python.org/downloads/>（Windows 安装时务必勾选 *Add python.exe to PATH*）
- **Node.js 20+** → <https://nodejs.org/>（Windows 也可执行 `winget install OpenJS.NodeJS.LTS`）

### 启动

Windows：直接双击 **`start.bat`**；或在项目目录执行：

```bash
python start.py
```

macOS / Linux：

```bash
bash start.sh        # 或 python3 start.py
```

首次启动会自动完成：安装后端依赖 → 生成 `.env` → 安装前端依赖 → 构建前端（约 3-10 分钟）→ 初始化数据库 → 创建管理员账号 → 启动前后端。之后每次启动只需几秒。

启动完成后终端会打印访问信息：

```
  ✓ StyleFlow 已启动
    本机访问      http://127.0.0.1:3000
    局域网访问    http://192.168.1.23:3000     ← 同一 WiFi 下手机/同事可直接打开
    接口文档      http://127.0.0.1:3000/api/v1/docs
    管理后台      http://127.0.0.1:8000/admin/   ← Django 后台（走后端端口）
    默认账号      admin / <随机密码，同时写入 data/管理员账号.txt>
```

按 `Ctrl+C` 停止；也可以另开窗口执行 `python start.py --stop`。

### 常用参数

| 参数 | 说明 |
|---|---|
| `--check` | 只做环境自检，不启动服务 |
| `--port 8080` | 更换前端端口（默认 3000） |
| `--local` | 仅本机可访问（默认允许局域网访问） |
| `--dev` | 前端开发模式（不构建，改代码即时生效） |
| `--rebuild` | 强制重新安装/构建前端 |
| `--db postgres` | 使用 PostgreSQL（读取 `.env` 中的 `DB_*`） |
| `--reset-admin` | 重置管理员密码并打印新密码 |
| `--stop` | 停止已启动的服务 |

### 数据与备份

数据库（SQLite）、上传与 AI 生成的图片、运行日志都集中在 **`data/`** 目录：

```
data/
├── styleflow.sqlite3     # 数据库（SQLite 模式）
├── media/                # 用户上传 / AI 生成的文件
├── static/               # 后台静态资源
└── logs/                 # backend.log / frontend.log
```

备份或换电脑时，拷走 `data/` 与 `.env` 两个东西即可。

### 三种访问方式

| 场景 | 做法 |
|---|---|
| **本机** | 直接启动，打开 http://127.0.0.1:3000 |
| **局域网** | 其他设备连同一 WiFi，打开终端打印的局域网地址（首次可能需放行防火墙 3000 端口，脚本会给出命令） |
| **公网 / 域名** | 见 [docs/部署/02-公网访问教程.md](docs/部署/02-公网访问教程.md)（Caddy 自动 HTTPS、Cloudflare Tunnel 等） |

更多说明：
- [本地一键运行详解](docs/部署/01-本地一键运行.md)
- [局域网访问配置](docs/部署/01-本地一键运行.md#6-局域网访问)
- [公网与域名访问](docs/部署/02-公网访问教程.md)
- [常见问题排查](docs/部署/03-常见问题.md)

---

## 🏗️ 技术栈

| 层级 | 技术 | 版本 / 说明 |
|------|------|------|
| **后端框架** | Django | 6.0 LTS |
| **API 框架** | Django Ninja | 1.6 |
| **异步任务** | 内置线程池 / Celery | 默认线程池（无需 Redis），可切 Celery 5.6 |
| **数据库** | SQLite / PostgreSQL | 默认 SQLite（零配置），可切 PostgreSQL 15 |
| **缓存/队列** | Redis | 可选，仅 Celery 模式需要 |
| **文件存储** | 本地磁盘 / S3 (MinIO) | 默认本地磁盘 `data/media`，可切 S3 兼容对象存储 |
| **前端框架** | Next.js | 16 |
| **UI 组件** | Ant Design | 5 |
| **AI 语言模型** | OpenAI / Claude / 通义千问 | 可选，自行配置 Key |
| **AI 图像模型** | Stable Diffusion / 通义万相 | 可选 |
| **虚拟试衣** | IDM-VTON (可接入) | 可选 |
| **运行方式** | 一键脚本 `start.py` | 本机 / 局域网 / 域名反向代理 |

---

## 📁 项目结构

```
StyleFlow/
├── start.py                    # ⭐ 一键启动器（本地/局域网零配置）
├── start.bat / start.sh        # Windows 双击 / macOS、Linux 入口
├── .env.example                # 运行配置示例（start.py 会自动生成 .env）
├── data/                       # 运行时数据（数据库/图片/日志，可整体备份）
├── backend/                    # Django 后端
│   ├── config/                 # 项目配置
│   │   ├── settings/           # base / local / dev / prod 四层配置
│   │   ├── api.py              # Ninja API 注册
│   │   └── celery_app.py       # Celery 配置（可选）
│   ├── apps/                   # 10 个业务模块
│   │   ├── accounts/           # 用户认证 + JWT
│   │   ├── design/             # AI 设计工坊
│   │   ├── tryon/              # 虚拟试衣
│   │   ├── techpack/           # 工艺单
│   │   ├── workflow/           # 工作流引擎
│   │   ├── costing/            # 核工价
│   │   ├── wages/              # 计件工资
│   │   ├── erp/                # ERP 对接
│   │   └── media/              # 媒体库
│   └── common/                 # 公共模块
│       ├── aiservice/          # AI 服务封装
│       ├── storage.py          # 文件存储服务（local / s3）
│       ├── taskqueue.py        # 任务执行桥接（线程池 / Celery）
│       └── crypto.py           # 加密工具
├── frontend/                   # Next.js 前端（同源反向代理后端）
│   ├── next.config.ts          # /api /media /admin 代理到 Django
│   └── src/app/                # 16 个页面路由
├── docs/
│   ├── design/                 # 设计文档
│   └── 部署/                   # 一键运行 / 局域网 / 公网 / 常见问题
└── data/logs/                  # backend.log、frontend.log
```

---

## 📸 页面一览

| 路由 | 页面 | 说明 |
|------|------|------|
| `/` | 首页 | 自动跳转 |
| `/login` | 登录 | JWT 认证 |
| `/register` | 注册 | 角色选择 |
| `/dashboard` | 工作台 | 概览 |
| `/design/generate` | AI 生成 | Prompt → 文生图 |
| `/design/gallery` | 设计稿库 | 个人/公共双 Tab |
| `/tryon` | 虚拟试衣 | 换装合成 |
| `/techpack` | 工艺单 | AI 生成/管理 |
| `/workflow` | 工作流 | 编辑器 + 看板 |
| `/costing` | 核工价 | 自动核算 |
| `/wages` | 计件工资 | 报表 |
| `/media` | 媒体库 | 素材管理 |
| `/admin/settings` | AI 配置 | 个人模型偏好 |
| `/admin/`（后端端口） | Django 管理后台 | 用户/数据管理：http://127.0.0.1:8000/admin/ |

---

## 🧪 开发计划

- [x] 用户认证 + JWT
- [x] AI 设计工坊（文生图/图生图）
- [x] 虚拟试衣
- [x] 可视化工作流引擎
- [x] 工艺单管理
- [x] 核工价 + 计件工资
- [x] 媒体库（自动入库/回收站/批量操作）
- [x] ERP 对接
- [x] 多 AI 模型支持
- [x] API Key 加密存储
- [x] 零配置一键运行（SQLite + 本地文件存储 + 进程内任务队列）
- [x] 前后端同源部署（局域网 IP / 域名访问无需改配置）
- [ ] 英文界面 (i18n)
- [ ] 微信小程序
- [ ] 单元测试 + E2E
- [ ] 在线 Demo 部署

---

## 🤝 参与贡献

欢迎提交 PR 和 Issue！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feat/amazing`)
3. 提交更改 (`git commit -m 'feat: 添加某个功能'`)
4. 推送到分支 (`git push origin feat/amazing`)
5. 提交 Pull Request

---

## 📄 许可证

[MIT License](LICENSE)

Copyright © 2026 雅典娜
