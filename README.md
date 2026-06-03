# RBAC 文件资源管理器

> 北京科技大学 2026 年春 · 软件安全实验课程项目  
> Role-Based Access Control — Web 端文件资源管理器

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-2.3-black.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/License-Coursework-lightgrey.svg)](#许可)

---

## 目录

- [项目简介](#项目简介)
- [从 GitHub 开始](#从-github-开始)
- [默认账号](#默认账号)
- [系统页面一览](#系统页面一览)
- [RBAC 权限模型](#rbac-权限模型)
- [架构设计](#架构设计)
- [项目结构](#项目结构)
- [API 概览](#api-概览)
- [安全设计](#安全设计)
- [课程任务要求对照](#课程任务要求对照)
- [文档索引](#文档索引)
- [许可](#许可)

---

## 项目简介

基于 **RBAC**（基于角色的访问控制）模型的 Web 端文件资源管理器。支持 **6 种角色**和 **13 个细粒度权限**，使用 SQLite 关系型数据库定义文件访问控制策略（读、写、更新、删除），并实施完整的安全管理措施。

### 功能特性

- **RBAC 模型**：用户 → 角色 → 权限 三级映射，6 种预定义角色，权限矩阵可视化编辑
- **用户管理**：注册、登录、角色分配、账号启停
- **角色管理**：创建/编辑/删除角色，可视化权限矩阵（复选框网格）
- **文件管理**：上传、下载、替换、删除，支持拖拽上传，UUID 安全存储
- **审计日志**：全操作记录（含权限拒绝），按操作类型/资源/时间筛选，分页浏览，不可删除
- **权限中间件**：`@require_permission` 装饰器，端点级 RBAC 强制校验，401/403 精确区分
- **安全管理**：bcrypt 哈希、JWT 认证、路径遍历防护、文件类型白名单、CSP 头、登录限流

### 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Python 3.10+ / Flask 2.3 |
| 数据库 | SQLite + SQLAlchemy ORM |
| 认证 | JWT (HS256)，24 小时过期 |
| 前端 | Bootstrap 5 + 原生 JavaScript (零框架依赖) |
| 安全 | bcrypt / werkzeug / Flask-Limiter |

### 项目统计

| 指标 | 数值 |
|------|:---:|
| 源文件 | 50+ |
| 代码行数 | 4,300+ |
| 后端模块 | 22 |
| 前端页面 | 7 |
| JavaScript 模块 | 7 |
| 测试文件 | 5 |
| 测试用例 | 117 |
| 数据库表 | 7 |
| API 端点 | 22 |

---

## 从 GitHub 开始

### 1. 克隆仓库

```bash
git clone https://github.com/THEST515/RBAC.git
cd RBAC
```

### 2. 创建虚拟环境（推荐）

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 初始化数据库

```bash
python init_db.py
```

执行后会创建 SQLite 数据库并写入种子数据：
- 13 条权限记录
- 6 个角色 + 权限映射
- 1 个默认管理员账号

### 5. 启动服务器

```bash
python app.py
```

浏览器打开 **http://localhost:5000**

### 6. 停止服务器

按 `Ctrl + C` 停止。

> **提示：** 重新初始化可删除 `instance/rbac.db` 后再次运行 `python init_db.py`。

---

## 默认账号

| 用户名 | 密码 | 角色 | 权限 |
|--------|------|------|:---:|
| `admin` | `admin123` | Admin | 全部 13 项 |

> ⚠️ **首次登录后请立即修改密码。**

---

## 系统页面一览

| 页面 | 路径 | 功能 |
|------|------|------|
| **登录** | `/login` | 用户名+密码登录，JWT 认证 |
| **注册** | `/register` | 新用户注册，默认分配 Viewer 角色 |
| **仪表盘** | `/` | 用户/角色/文件/操作统计卡片 + 最近操作列表 |
| **用户管理** | `/users` | 用户增删改查、角色分配、账号启停 |
| **角色管理** | `/roles` | 角色增删改、权限矩阵（复选框网格） |
| **文件管理** | `/files` | 文件上传/下载/替换/删除，拖拽上传 |
| **审计日志** | `/audit` | 操作记录浏览，按类型/资源/日期筛选，分页 |

页面根据登录用户的权限**自动显示/隐藏**导航菜单和操作按钮。

---

## RBAC 权限模型

### 角色权限矩阵

| 权限 | Admin | Manager | Editor | Contributor | Viewer | Auditor |
|------|:-----:|:-------:|:------:|:-----------:|:------:|:-------:|
| user:create | ✅ | ✅ | — | — | — | — |
| user:read | ✅ | ✅ | ✅ | — | — | — |
| user:update | ✅ | ✅ | — | — | — | — |
| user:delete | ✅ | ✅ | — | — | — | — |
| role:create | ✅ | — | — | — | — | — |
| role:read | ✅ | ✅ | — | — | — | — |
| role:update | ✅ | — | — | — | — | — |
| role:delete | ✅ | — | — | — | — | — |
| file:create | ✅ | ✅ | ✅ | ✅ | — | — |
| file:read | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| file:update | ✅ | ✅ | ✅ | ✅ | — | — |
| file:delete | ✅ | ✅ | ✅ | — | — | — |
| audit:read | ✅ | ✅ | — | — | — | ✅ |

### 角色说明

| 角色 | 权限数 | 描述 |
|------|:-----:|------|
| **Admin** 管理员 | 13 | 完全系统控制 — 管理用户、角色、文件，查看审计日志 |
| **Manager** 经理 | 10 | 用户管理和角色查看，所有文件操作，查看审计日志 |
| **Editor** 编辑者 | 5 | 完整文件 CRUD 操作，可查看用户列表 |
| **Contributor** 贡献者 | 3 | 文件上传和编辑，不可删除 |
| **Viewer** 浏览者 | 1 | 只读文件访问 |
| **Auditor** 审计员 | 2 | 查看审计日志和文件 |

---

## 架构设计

### 系统架构

```
┌─────────────────────────────────────────────────┐
│                    浏览器                         │
│  ┌──────────┬──────────┬──────────┬───────────┐  │
│  │ 仪表盘   │ 用户管理  │ 角色管理  │ 文件管理  │  │
│  │ 登录注册 │ 审计日志  │          │          │  │
│  └──────────┴──────────┴──────────┴───────────┘  │
└────────────────────┬────────────────────────────┘
                     │ HTTP + JWT
┌────────────────────▼────────────────────────────┐
│                Flask 应用层                       │
│  ┌──────────────────────────────────────────┐   │
│  │         @require_permission              │   │
│  │     (权限装饰器 — 端点级 RBAC 校验)       │   │
│  └──────────────────────────────────────────┘   │
│  ┌──────────┬──────────┬───────────────────┐    │
│  │ 路由层   │ 服务层   │ 中间件             │    │
│  │ routes/  │ services/│ middleware/        │    │
│  └──────────┴──────────┴───────────────────┘    │
└────────────────────┬────────────────────────────┘
                     │ SQLAlchemy ORM
┌────────────────────▼────────────────────────────┐
│              SQLite 数据库                        │
│  ┌──────┬──────┬───────────┬──────────┬───────┐ │
│  │users │roles │permissions│role_perm │ files │ │
│  │      │      │           │user_roles│       │ │
│  └──────┴──────┴───────────┴──────────┴───────┘ │
│  ┌──────────┐                                    │
│  │audit_logs│ (不可删除)                          │
│  └──────────┘                                    │
└─────────────────────────────────────────────────┘
```

### 分层设计

| 层 | 职责 | 目录 |
|----|------|------|
| **路由层** | HTTP 请求/响应处理，参数提取 | `routes/` |
| **服务层** | 业务逻辑，数据校验，审计日志 | `services/` |
| **模型层** | 数据库表定义，ORM 映射 | `models/` |
| **中间件** | JWT 解码，权限校验装饰器 | `middleware/` |
| **工具层** | 密码哈希，JWT 编解码，输入验证 | `utils/` |

### 请求处理流程

```
HTTP 请求
  │
  ├─ 1. Flask 路由匹配
  │
  ├─ 2. @require_permission 装饰器
  │     ├─ 提取 Authorization: Bearer <token>
  │     ├─ decode_token() 验证签名+过期
  │     ├─ 检查 permission ∈ payload.permissions
  │     ├─ 失败 → 记录审计日志 → 返回 401/403
  │     └─ 通过 → g.current_user = payload
  │
  ├─ 3. 路由处理函数
  │     └─ 提取请求参数
  │
  ├─ 4. 服务层处理
  │     ├─ 输入验证 (validators.py)
  │     ├─ 业务逻辑
  │     └─ 审计日志 (audit_service.py)
  │
  ├─ 5. ORM 数据库操作
  │     └─ 参数化查询，防 SQL 注入
  │
  ├─ 6. 安全响应头注入
  │     └─ CSP / X-Frame-Options / X-Content-Type-Options
  │
  └─ 7. JSON 响应返回
```

---

## 项目结构

```
RBVC/
├── app.py                    # Flask 应用工厂 + 入口
├── config.py                 # 配置类（开发/生产）
├── extensions.py             # SQLAlchemy 共享实例（避免循环导入）
├── init_db.py                # 数据库初始化 + 种子数据
├── requirements.txt          # Python 依赖
│
├── models/                   # 数据模型（ORM 映射）
│   ├── user.py               # 用户 — has_permission() 方法驱动 RBAC
│   ├── role.py               # 角色 — 多对多关联权限
│   ├── permission.py         # 权限 — resource:action 命名
│   ├── file_model.py         # 文件元数据 — UUID 磁盘存储
│   └── audit_log.py          # 审计日志 — 不可删除
│
├── routes/                   # API 路由（HTTP 层）
│   ├── auth.py               # POST /api/auth/login, register, GET profile
│   ├── users.py              # CRUD /api/users + 角色分配
│   ├── roles.py              # CRUD /api/roles + 权限矩阵
│   ├── permissions.py        # GET /api/permissions
│   ├── files.py              # CRUD /api/files + multipart 上传下载
│   └── audit.py              # GET /api/audit-logs 筛选分页
│
├── services/                 # 业务逻辑层
│   ├── auth_service.py       # 注册/登录/个人信息逻辑
│   ├── user_service.py       # 用户 CRUD + 角色分配逻辑
│   ├── role_service.py       # 角色 CRUD + 权限管理逻辑
│   ├── file_service.py       # 文件安全操作 + 路径防护
│   └── audit_service.py      # 日志写入 + 筛选查询
│
├── middleware/
│   └── permissions.py        # require_permission 装饰器 + get_current_user
│
├── utils/
│   ├── security.py           # bcrypt 密码哈希 + JWT 编解码
│   └── validators.py         # 用户名/密码/邮箱/文件类型验证
│
├── templates/                # Jinja2 前端页面
│   ├── base.html             # Bootstrap 5 基础布局（导航栏+安全头）
│   ├── login.html            # 登录表单
│   ├── register.html         # 注册表单
│   ├── dashboard.html        # 统计仪表盘
│   ├── users.html            # 用户管理表格 + 模态框
│   ├── roles.html            # 角色表格 + 权限矩阵
│   ├── files.html            # 文件列表 + 上传拖拽区
│   └── audit.html            # 审计日志 + 筛选栏
│
├── static/
│   ├── css/style.css         # 自定义样式
│   └── js/
│       ├── api.js            # 统一 fetch 封装 + JWT 管理 + 权限联动
│       ├── auth.js           # 登录/注册表单提交
│       ├── dashboard.js      # 仪表盘统计数据加载
│       ├── users.js          # 用户增删改查 + 角色复选框
│       ├── roles.js          # 角色管理 + 权限矩阵编辑
│       ├── files.js          # 文件上传/下载/替换/删除 + 拖拽
│       └── audit.js          # 审计日志筛选 + 分页 + 操作名中文化
│
├── tests/                    # 单元测试（pytest）
│   ├── conftest.py           # 共享 fixtures（app/client/auth tokens）
│   ├── test_auth.py          # 认证测试（15 用例）
│   ├── test_users.py         # 用户管理测试（12 用例）
│   ├── test_roles.py         # 角色管理测试（12 用例）
│   ├── test_files.py         # 文件操作测试（12 用例）
│   └── test_permissions.py   # RBAC 权限矩阵全排列（66 用例）
│
├── uploads/                  # 文件存储目录（UUID 命名，.gitignore）
│
├── README.md                 # 项目说明（本文件）
├── safe.md                   # 安全管理功能详解
└── 课程设计讲解文档.md         # 课程设计原理讲解（非 GitHub）
```

---

## API 概览

所有 API 端点位于 `/api` 前缀下。除登录/注册外，均需 `Authorization: Bearer <token>` 请求头。

### 认证

| 方法 | 端点 | 认证 | 说明 |
|------|------|:----:|------|
| POST | `/api/auth/register` | — | 注册新用户（默认 Viewer 角色） |
| POST | `/api/auth/login` | — | 登录，返回 JWT + 用户信息 |
| GET | `/api/auth/profile` | JWT | 获取当前用户详情 |

### 用户管理

| 方法 | 端点 | 权限 |
|------|------|------|
| GET | `/api/users` | `user:read` |
| POST | `/api/users` | `user:create` |
| GET | `/api/users/<id>` | `user:read` |
| PUT | `/api/users/<id>` | `user:update` |
| DELETE | `/api/users/<id>` | `user:delete` |
| PUT | `/api/users/<id>/roles` | `user:update` |

### 角色管理

| 方法 | 端点 | 权限 |
|------|------|------|
| GET | `/api/roles` | `role:read` |
| POST | `/api/roles` | `role:create` |
| GET | `/api/roles/<id>` | `role:read` |
| PUT | `/api/roles/<id>` | `role:update` |
| DELETE | `/api/roles/<id>` | `role:delete` |
| GET | `/api/roles/<id>/permissions` | `role:read` |
| PUT | `/api/roles/<id>/permissions` | `role:update` |

### 文件管理

| 方法 | 端点 | 权限 | 说明 |
|------|------|------|------|
| GET | `/api/files` | `file:read` | 文件列表 |
| POST | `/api/files` | `file:create` | 上传（multipart/form-data） |
| GET | `/api/files/<id>` | `file:read` | 下载文件（`Content-Disposition: attachment`） |
| GET | `/api/files/<id>/info` | `file:read` | 文件元数据 |
| PUT | `/api/files/<id>` | `file:update` | 替换文件内容 |
| DELETE | `/api/files/<id>` | `file:delete` | 删除文件 |

### 审计日志

| 方法 | 端点 | 权限 |
|------|------|------|
| GET | `/api/audit-logs` | `audit:read` |

支持的查询参数：`?user_id=&action=&resource_type=&start_date=&end_date=&page=&per_page=`

### 权限列表

| 方法 | 端点 | 认证 |
|------|------|:----:|
| GET | `/api/permissions` | JWT |

---

## 安全设计

详细安全分析见 **[safe.md](safe.md)**。

| 类别 | 安全项 | 实现 |
|------|--------|------|
| **认证** | 密码哈希 | bcrypt (werkzeug) |
| | JWT 签名 | HS256，24h 过期，payload 含权限 |
| | 密码复杂度 | ≥8 位 + 大写 + 小写 + 数字 |
| | 登录限流 | 5 次/分钟/IP |
| **鉴权** | 端点级 RBAC | `@require_permission` 装饰器 |
| | 状态码区分 | 无 token → 401，无权限 → 403 |
| | 前端联动 | 导航栏/按钮根据权限自动显隐 |
| **文件安全** | 上传白名单 | 13 种安全类型，拒绝可执行文件 |
| | 路径遍历 | `os.path.realpath()` 边界检查 |
| | 文件重命名 | UUID 磁盘存储，防恶意文件名 |
| | 大小限制 | 16MB，超限返回 413 |
| **Web 防护** | XSS | Jinja2 转义 + CSP 头 + escapeHtml() |
| | Clickjacking | `X-Frame-Options: DENY` |
| | MIME 嗅探 | `X-Content-Type-Options: nosniff` |
| | CSRF | JWT 在 Header（非 Cookie），天然免疫 |
| | SQL 注入 | SQLAlchemy ORM 参数化查询 |
| **审计** | 全操作记录 | 创建/更新/删除/登录全部入库 |
| | 拒绝记录 | 权限不足的尝试也写入日志 |
| | 不可删除 | 审计表无 DELETE 端点 |

---

## 课程任务要求对照

| 任务要求 | 状态 | 实现 |
|----------|:----:|------|
| 支持不少于 6 个角色和权限 | ✅ | 6 角色 / 13 权限 |
| 数据库定义文件访问控制 | ✅ | SQLite 7 表，file:CRUD 完整实现 |
| 前端用户界面 | ✅ | 7 页面：登录/注册/仪表盘/用户/角色/文件/审计 |
| 后端认证与权限验证 | ✅ | Flask + JWT + `@require_permission` 全覆盖 |
| RBAC 模型：角色-权限映射 | ✅ | role_permissions 多对多表 + 可视化矩阵编辑 |
| 角色创建、删除、权限分配 | ✅ | 完整 CRUD + 权限矩阵复选框批量分配 |
| Web 端资源管理器 | ✅ | 文件上传/下载/替换/删除，拖拽上传 |
| 安全管理功能 | ✅ | 7 大类 22 项，详见 [safe.md](safe.md) |
| 数据库方案（非区块链） | ✅ | SQLite + SQLAlchemy ORM |
| 客户与服务器分离 | ✅ | 浏览器前端 ↔ Flask 后端，HTTP + JWT |
| SSL 双向认证 | ⬜ | 可选加分项 |
| 单元测试/集成测试 | ✅ | pytest 117 用例，6 角色 × 10 端点全排列验证 |
| SSL 双向认证 | ⬜ | 可选加分项 |
| 云平台部署 | ⬜ | 可部署至任意支持 Python 的云服务器 |

---

## 运行测试

```bash
cd RBVC

# 安装测试依赖
pip install pytest

# 运行全部 117 个测试用例
python -m pytest tests/ -v

# 简洁输出
python -m pytest tests/ -q

# 只跑权限矩阵测试
python -m pytest tests/test_permissions.py -v
```

```
tests/test_auth.py ............ 15 passed
tests/test_users.py ........... 12 passed
tests/test_roles.py ........... 12 passed
tests/test_files.py ........... 12 passed
tests/test_permissions.py .... 66 passed
========================= 117 passed in 108s =========================
```

---

## 文档索引

| 文档 | 说明 |
|------|------|
| [README.md](README.md) | 项目总览、快速开始、架构、API（本文件） |
| [safe.md](safe.md) | 安全管理功能详解：7 大类 22 项措施 + 攻击场景防御表 |
| 课程设计讲解文档.md | 课程设计原理详解：RBAC 模型、数据库设计、认证流程、安全机制（非 GitHub） |

---

## 许可

本项目为北京科技大学 2026 年春季《软件安全实验》课程作业，仅供学习参考。

**作者：** Mamingkang  
**GitHub：** [THEST515/RBAC](https://github.com/THEST515/RBAC)
