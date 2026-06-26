<p align="center">
  <img src="https://img.shields.io/badge/license-MIT-blue" alt="License">
  <img src="https://img.shields.io/badge/python-3.11%2B-blue" alt="Python">
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
  <a href="#-快速开始">快速开始</a> •
  <a href="#-功能特性">功能特性</a> •
  <a href="#-技术栈">技术栈</a> •
  <a href="#-项目结构">项目结构</a> •
  <a href="#-部署">部署</a> •
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

## 🚀 快速开始

### 前置要求
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Redis 7+

### 1. 克隆项目
```bash
git clone https://github.com/Athenavi/StyleFlow.git
cd StyleFlow
```

### 2. 后端启动
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements/dev.txt

# 配置环境变量（也可直接修改 .env）
cp .env.example .env
# 编辑 .env 填写数据库等配置

# 初始化数据库
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser

# 启动开发服务器
python manage.py runserver
# API 文档 → http://localhost:8000/api/docs
```

### 3. 前端启动
```bash
cd frontend
npm install
npm run dev
# 浏览器打开 → http://localhost:3000
```

### 4. 一键 Docker 部署
```bash
docker compose up -d
```

---

## 🏗️ 技术栈

| 层级 | 技术 | 版本 |
|------|------|------|
| **后端框架** | Django | 6.0 LTS |
| **API 框架** | Django Ninja | 1.6 |
| **异步任务** | Celery | 5.6 |
| **数据库** | PostgreSQL | 15 |
| **缓存/队列** | Redis | 7 |
| **对象存储** | MinIO (S3 兼容) | latest |
| **前端框架** | Next.js | 16 |
| **UI 组件** | Ant Design | 5 |
| **AI 语言模型** | OpenAI / Claude / 通义千问 | - |
| **AI 图像模型** | Stable Diffusion / 通义万相 | - |
| **虚拟试衣** | IDM-VTON (可接入) | - |

---

## 📁 项目结构

```
StyleFlow/
├── backend/                    # Django 后端
│   ├── config/                 # 项目配置
│   │   ├── settings/           # base/dev/prod 三层配置
│   │   ├── api.py              # Ninja API 注册
│   │   └── celery_app.py       # Celery 配置
│   ├── apps/                   # 9 个业务模块
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
│       ├── storage.py          # 文件存储服务
│       └── crypto.py           # 加密工具
├── frontend/                   # Next.js 前端
│   └── src/app/                # 16 个页面路由
│       ├── (auth)/             # 登录/注册
│       └── (dashboard)/        # 10+ 业务页面
├── docs/design/                # 11 份设计文档
└── docker-compose.yml          # 6 服务编排
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
