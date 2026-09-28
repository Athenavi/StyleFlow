<p align="center">
  <img src="https://img.shields.io/badge/license-MIT-blue" alt="License">
  <img src="https://img.shields.io/badge/python-3.12%2B-blue" alt="Python">
  <img src="https://img.shields.io/badge/django-6.0-green" alt="Django">
  <img src="https://img.shields.io/badge/next.js-16-purple" alt="Next.js">
</p>

<h1 align="center">🎨 StyleFlow</h1>
<p align="center"><b>AI 驱动的服装设计-生产协同平台</b></p>

<p align="center">
  <i>让灵感自然涌动，让流程自如流转。</i>
</p>

---

## ✨ 功能特性

| 模块 | 能力 |
|---|---|
| **AI 设计工坊** | 文生图 / 图生图，设计稿与版本管理，5 套提示词模板，多模型可切（OpenAI / Claude / 通义千问） |
| **虚拟试衣** | 人物图 + 服装图合成试穿效果（当前为模拟流程，可接 IDM-VTON / OOTDiffusion） |
| **工艺单** | AI 生成工艺单：尺码表、工序列表、面料说明 + 审核流程 |
| **可视化工作流** | 拖拽式节点编排、角色认领、自动推进、待办看板、内置模板（最多 10 条自定义流程） |
| **核工价 / 计件工资** | 工序模板匹配自动核算，工资报表与统计看板 |
| **媒体库** | 上传分类（6 类，单文件 ≤10MB）、批量操作、回收站、试衣结果自动入库 |
| **ERP 对接** | 数据库直连同步款式与工序标准，支持回写 |
| **账号与安全** | JWT 认证（30min / 7d）、6 种角色权限、API Key 双层 Fernet 加密 |

## 🚀 快速开始（零配置）

只需要 **Python 3.12+** 与 **Node.js 20+**：
<https://www.python.org/downloads/>（Windows 安装时勾选 *Add python.exe to PATH*）、<https://nodejs.org/>。

```bash
# Windows：双击 start.bat，或
python start.py
# macOS / Linux
bash start.sh
```

首次启动自动完成：创建虚拟环境 → 安装依赖 → 生成 `.env` → 构建前端（3-10 分钟，之后秒启）→ 建库 → 创建管理员 → 启动服务。停止：`Ctrl+C` 或 `python start.py --stop`。

```
本机访问    http://127.0.0.1:3000
局域网访问  http://192.168.1.23:3000
接口文档    http://127.0.0.1:3000/api/v1/docs
管理后台    http://127.0.0.1:8000/admin/
默认账号    admin / <随机密码，见 data/管理员账号.txt>
```

常用参数：`--check` 自检 · `--port 8080` 换端口 · `--local` 仅本机 · `--dev` 前端开发模式 · `--db postgres` 用 PostgreSQL · `--reset-admin` 重置密码 · `--rebuild` 重装重建 · `--stop` 停止。

数据（数据库、图片、日志）都在 `data/`，备份 = 拷走 `data/` + `.env`。

👉 完整说明、局域网与公网/域名部署、常见问题排查：**[docs/运行与部署.md](docs/运行与部署.md)**

## 🏗️ 技术栈

| 层级 | 技术 | 说明 |
|---|---|---|
| 后端 | Django 6 + Django Ninja | `/api/v1`，Pydantic v2 序列化 |
| 数据库 | SQLite / PostgreSQL | 默认 SQLite（零配置），可一键切换 |
| 任务 | 进程内线程池 / Celery | 默认线程池，无需 Redis |
| 文件 | 本地磁盘 / S3·MinIO | 默认 `data/media` |
| 前端 | Next.js 16 + Ant Design + zustand | 同源代理 `/api`、`/media`、`/static` |
| AI | OpenAI / Claude / 通义千问 / 通义万相 / SD WebUI | 需自备 API Key 或本地模型 |

## 📁 项目结构

```
StyleFlow/
├── start.py / start.bat / start.sh   # 一键启动器
├── .env.example                      # 运行配置示例（start.py 自动生成 .env）
├── data/                             # 运行期数据：数据库、图片、日志、备份对象
├── backend/
│   ├── config/settings/              # base / local / dev / prod
│   ├── apps/                         # accounts design tryon techpack workflow
│   │                                 # costing wages erp media planning
│   └── common/                       # storage 文件存储 · taskqueue 任务桥接
│                                     # aiservice AI 封装 · crypto 加密
├── frontend/
│   ├── next.config.ts                # /api、/media、/static 同源代理
│   └── src/app/                      # 业务页面
└── docs/
    ├── 运行与部署.md                  # 一键运行 · 局域网 · 公网 · 常见问题
    └── 设计摘要.md                    # 架构、模块、API 与 AI 约定
```

## 📄 许可证

[MIT License](LICENSE) · Copyright © 2026 雅典娜
