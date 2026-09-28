<p align="center">
  <img src="https://img.shields.io/badge/license-MIT-blue" alt="License">
  <img src="https://img.shields.io/badge/python-3.12%2B-blue" alt="Python">
  <img src="https://img.shields.io/badge/django-6.0%2B-green" alt="Django">
  <img src="https://img.shields.io/badge/next.js-16-purple" alt="Next.js">
  <img src="https://img.shields.io/badge/PRs-welcome-brightgreen" alt="PRs Welcome">
</p>

<h1 align="center">🎨 StyleFlow</h1>
<p align="center"><b>AI-Powered Fashion Design & Production Collaboration Platform</b></p>

<p align="center">
  <i>Let inspiration flow naturally, let processes run smoothly.</i>
</p>

<p align="center">
  <a href="#-quick-start-zero-configuration">Quick Start</a> •
  <a href="#-features">Features</a> •
  <a href="#-tech-stack">Tech Stack</a> •
  <a href="#-project-structure">Structure</a> •
  <a href="docs/部署/01-本地一键运行.md">Deployment (中文)</a> •
  <a href="README.md">中文</a>
</p>

---

## ✨ Features

### 🤖 AI Design Studio
| Feature | Description |
|---------|-------------|
| **Text-to-Image** | Generate fashion designs from prompts (5 presets) |
| **Image-to-Image** | Upload reference images, style transfer via ControlNet |
| **Design Management** | Personal gallery, categories, version history |
| **Multi-Model** | Switch between OpenAI / Claude / Tongyi Qwen |

### 👗 Virtual Try-On
| Feature | Description |
|---------|-------------|
| **Synthesis** | Person + Garment → AI composite wearing effect |
| **Media Library** | Pick materials from library, one-click import |
| **Samples** | Built-in sample images for quick try |
| **Auto-Archive** | Results automatically saved to media library |

### 📋 Tech Pack Management
- AI-generated tech packs (LLM parameter extraction + process template matching)
- Size specs, process steps, fabric descriptions
- Review workflow

### 🔄 Visual Workflow Engine
- **Visual Editor**: Drag-and-drop node orchestration, up to 10 custom workflows
- **Role-based Access**: Claim mechanism (first-come-first-served), handler_role permission checks
- **Auto-Proceed**: auto_proceed nodes advance automatically
- **Built-in Templates**: Style Development / Material Approval / AI-Assisted Design
- **Kanban Board**: Claim / Process / Approve / Reject

### 📁 Media Library
- Supports JPG / PNG / WebP / GIF, ≤10MB per file
- 6 categories: Model / Garment / Fabric / Sketch / Moodboard / Other
- Batch operations: batch categorize, batch delete
- Trash: file-level recycle (moves to .trash directory)
- Pagination

### 📊 Costing & Piece-Rate Wages
- Process template matching, automatic cost calculation
- Wage reports: filter by worker ID, date range
- Dashboard: total workers / total amount / total quantity

### 🔗 ERP Integration
- Direct database sync engine
- Style data mirror + process standard data
- Write-back mechanism

### 🛡️ Security
| Feature | Description |
|---------|-------------|
| API Key Encryption | Fernet dual-layer encryption (env key + user password) |
| Password Change → Key Revocation | Old keys become undecryptable |
| JWT Auth | Access Token 30min + Refresh Token 7d |
| Role-Based Access | 6 roles, menu-level + API-level permissions |

---

## 🚀 Quick Start (Zero Configuration)

> No PostgreSQL / Redis / MinIO to install, no virtualenv to create, no credentials to fill in.
> The launcher script prepares everything, initializes the database, builds the frontend and starts both services.

### Prerequisites (only two)

- **Python 3.12+** → <https://www.python.org/downloads/> (on Windows, tick *Add python.exe to PATH*)
- **Node.js 20+** → <https://nodejs.org/> (or `winget install OpenJS.NodeJS.LTS` on Windows)

### Run it

Windows: double-click **`start.bat`**, or from the project root:

```bash
python start.py
```

macOS / Linux:

```bash
bash start.sh        # or python3 start.py
```

The first run installs backend dependencies, generates `.env`, installs frontend dependencies, builds the frontend (3-10 minutes), creates the database (SQLite), sets up an admin account and starts both services. Later runs take only a few seconds.

```
  ✓ StyleFlow is running
    Local         http://127.0.0.1:3000
    LAN           http://192.168.1.23:3000     ← open this from any device on the same Wi-Fi
    API docs      http://127.0.0.1:3000/api/v1/docs
    Django admin  http://127.0.0.1:8000/admin/   (served on the backend port)
    Account       admin / <random password, also saved to data/管理员账号.txt>
```

Press `Ctrl+C` to stop, or run `python start.py --stop` from another terminal.

### Useful flags

| Flag | Description |
|---|---|
| `--check` | Environment self-check only, do not start |
| `--port 8080` | Change the frontend port |
| `--local` | Bind to 127.0.0.1 only (LAN access is allowed by default) |
| `--dev` | Frontend dev mode (no build, hot reload) |
| `--rebuild` | Force reinstall / rebuild the frontend |
| `--db postgres` | Use PostgreSQL (reads `DB_*` from `.env`) |
| `--reset-admin` | Reset the admin password and print it |
| `--stop` | Stop the running instance |

### Data & backup

SQLite database, uploaded/generated images and logs all live in **`data/`**:

```
data/
├── styleflow.sqlite3     # database (SQLite mode)
├── media/                # uploads and AI output
├── static/               # admin static assets
└── logs/                 # backend.log / frontend.log
```

Copy `data/` and `.env` to move or back up the whole instance.

### Three ways to access

| Scenario | How |
|---|---|
| **Local machine** | Start and open http://127.0.0.1:3000 |
| **LAN** | Connect other devices to the same Wi-Fi and open the printed LAN URL (may require allowing the port through the firewall — the script prints the command) |
| **Public / domain** | See [docs/部署/02-公网访问教程.md](docs/部署/02-公网访问教程.md) (Caddy auto-HTTPS, Cloudflare Tunnel, …) |

Documentation: [本地一键运行](docs/部署/01-本地一键运行.md) · [公网与域名](docs/部署/02-公网访问教程.md) · [常见问题](docs/部署/03-常见问题.md)

---

## 🏗️ Tech Stack

| Layer | Technology | Version / Notes |
|-------|-----------|---------|
| **Backend** | Django | 6.0 LTS |
| **API** | Django Ninja | 1.6 |
| **Async Tasks** | in-process thread pool / Celery | thread pool by default (no Redis needed) |
| **Database** | SQLite / PostgreSQL | SQLite by default (zero config) |
| **Cache/Queue** | Redis | Optional, only for Celery mode |
| **Storage** | local disk / S3 (MinIO) | local `data/media` by default |
| **Frontend** | Next.js | 16 |
| **UI Library** | Ant Design | 5 |
| **LLM** | OpenAI / Claude / Tongyi Qwen | optional, bring your own key |
| **Image AI** | Stable Diffusion / Tongyi Wanxiang | optional |
| **Virtual Try-On** | IDM-VTON (pluggable) | optional |
| **Launcher** | `start.py` | local / LAN / reverse-proxied domain |

---

## 📁 Project Structure

```
StyleFlow/
├── start.py                    # one-click launcher (zero config)
├── start.bat / start.sh        # Windows / macOS+Linux entry points
├── .env.example                # runtime config sample (start.py writes .env)
├── data/                       # runtime data (db / media / logs)
├── backend/                    # Django backend
│   ├── config/                 # project config
│   │   ├── settings/           # base / local / dev / prod
│   │   ├── api.py              # Ninja API router
│   │   └── celery_app.py       # Celery config (optional)
│   ├── apps/                   # 10 business modules
│   │   ├── accounts/           # Auth + JWT
│   │   ├── design/             # AI design studio
│   │   ├── tryon/              # Virtual try-on
│   │   ├── techpack/           # Tech packs
│   │   ├── workflow/           # Workflow engine
│   │   ├── costing/            # Cost calculation
│   │   ├── wages/              # Piece-rate wages
│   │   ├── erp/                # ERP integration
│   │   └── media/              # Media library
│   └── common/                 # shared modules
│       ├── aiservice/          # AI service abstraction
│       ├── storage.py          # file storage (local / s3)
│       ├── taskqueue.py        # task bridge (thread pool / Celery)
│       └── crypto.py           # encryption utilities
├── frontend/                   # Next.js frontend (same-origin proxy to Django)
│   ├── next.config.ts          # proxies /api /media /admin to Django
│   └── src/app/                # 16 page routes
└── docs/                       # design docs + deployment guides
```

---

## 📸 Pages

| Route | Page | Description |
|-------|------|-------------|
| `/` | Home | Auto redirect |
| `/login` | Login | JWT authentication |
| `/register` | Register | Role selection |
| `/dashboard` | Dashboard | Overview |
| `/design/generate` | AI Generate | Prompt → Image |
| `/design/gallery` | Design Gallery | Personal/Public tabs |
| `/tryon` | Virtual Try-On | Garment synthesis |
| `/techpack` | Tech Packs | AI generation / management |
| `/workflow` | Workflow | Editor + Kanban |
| `/costing` | Costing | Auto calculation |
| `/wages` | Wages | Reports |
| `/media` | Media Library | Asset management |
| `/admin/settings` | AI Settings | Personal model preferences |
| `/admin/` (backend port) | Django Admin | Users & data: http://127.0.0.1:8000/admin/ |

---

## 🧪 Roadmap

- [x] User Auth + JWT
- [x] AI Design Studio (text2img/img2img)
- [x] Virtual Try-On
- [x] Visual Workflow Engine
- [x] Tech Pack Management
- [x] Costing + Piece-Rate Wages
- [x] Media Library (auto-archive / trash / batch ops)
- [x] ERP Integration
- [x] Multi-AI Model Support
- [x] API Key Encryption
- [x] Zero-config launcher (SQLite + local storage + in-process tasks)
- [x] Same-origin deployment (LAN IP / domain work without config changes)
- [ ] i18n (English UI)
- [ ] WeChat Mini Program
- [ ] Unit Tests + E2E
- [ ] Online Demo Deployment

---

## 🤝 Contributing

PRs and Issues are welcome!

1. Fork the repo
2. Create your feature branch (`git checkout -b feat/amazing`)
3. Commit changes (`git commit -m 'feat: add amazing feature'`)
4. Push (`git push origin feat/amazing`)
5. Open a Pull Request

---

## 📄 License

[MIT License](LICENSE)

Copyright © 2026 Athena
