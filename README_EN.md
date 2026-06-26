<p align="center">
  <img src="https://img.shields.io/badge/license-MIT-blue" alt="License">
  <img src="https://img.shields.io/badge/python-3.11%2B-blue" alt="Python">
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
  <a href="#-quick-start">Quick Start</a> •
  <a href="#-features">Features</a> •
  <a href="#-tech-stack">Tech Stack</a> •
  <a href="#-project-structure">Structure</a> •
  <a href="#-deployment">Deployment</a> •
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

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Redis 7+

### 1. Clone
```bash
git clone https://github.com/Athenavi/StyleFlow.git
cd StyleFlow
```

### 2. Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements/dev.txt

cp .env.example .env
# Edit .env with your database config

python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser

python manage.py runserver
# API docs → http://localhost:8000/api/docs
```

### 3. Frontend
```bash
cd frontend
npm install
npm run dev
# Open → http://localhost:3000
```

### 4. Docker
```bash
docker compose up -d
```

---

## 🏗️ Tech Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| **Backend** | Django | 6.0 LTS |
| **API** | Django Ninja | 1.6 |
| **Async Tasks** | Celery | 5.6 |
| **Database** | PostgreSQL | 15 |
| **Cache/Queue** | Redis | 7 |
| **Storage** | MinIO (S3 compatible) | latest |
| **Frontend** | Next.js | 16 |
| **UI Library** | Ant Design | 5 |
| **LLM** | OpenAI / Claude / Tongyi Qwen | - |
| **Image AI** | Stable Diffusion / Tongyi Wanxiang | - |
| **Virtual Try-On** | IDM-VTON (pluggable) | - |

---

## 📁 Project Structure

```
StyleFlow/
├── backend/                    # Django backend
│   ├── config/                 # Project config
│   │   ├── settings/           # base/dev/prod
│   │   ├── api.py              # Ninja API router
│   │   └── celery_app.py       # Celery config
│   ├── apps/                   # 9 business modules
│   │   ├── accounts/           # Auth + JWT
│   │   ├── design/             # AI design studio
│   │   ├── tryon/              # Virtual try-on
│   │   ├── techpack/           # Tech packs
│   │   ├── workflow/           # Workflow engine
│   │   ├── costing/            # Cost calculation
│   │   ├── wages/              # Piece-rate wages
│   │   ├── erp/                # ERP integration
│   │   └── media/              # Media library
│   └── common/                 # Shared modules
│       ├── aiservice/          # AI service abstraction
│       ├── storage.py          # File storage service
│       └── crypto.py           # Encryption utilities
├── frontend/                   # Next.js frontend
│   └── src/app/                # 16 page routes
│       ├── (auth)/             # Login/Register
│       └── (dashboard)/        # 10+ business pages
├── docs/design/                # 11 design documents
└── docker-compose.yml          # 6-service orchestration
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
