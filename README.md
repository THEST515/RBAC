# RBAC 文件资源管理器

> 北京科技大学 2026 年春 · 软件安全实验课程项目  
> Role-Based Access Control — Web 端文件资源管理器

## 项目简介

基于 **RBAC**（基于角色的访问控制）模型的 Web 端文件资源管理器。支持 6 种角色和 13 个细粒度权限，使用关系型数据库定义文件访问控制策略（读、写、更新、删除），前端提供类资源管理器界面。

### 功能特性

- **RBAC 模型**：用户 → 角色 → 权限 三级映射，6 种预定义角色
- **用户管理**：注册、登录、角色分配、账号启停
- **角色管理**：创建/编辑/删除角色，权限矩阵可视化分配
- **文件管理**：上传、下载、替换、删除，支持拖拽上传
- **审计日志**：全操作记录，支持按操作类型/资源/时间筛选和分页
- **权限中间件**：`@require_permission` 装饰器，端点级 RBAC 强制校验
- **安全措施**：bcrypt 密码哈希、JWT 认证、路径遍历防护、文件类型白名单、CSP 头

---

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Python 3 + Flask 2.3 |
| 数据库 | SQLite + SQLAlchemy ORM |
| 认证 | JWT (HS256)，24 小时过期 |
| 前端 | Bootstrap 5 + 原生 JavaScript |
| 安全 | bcrypt、werkzeug secure_filename、Flask-Limiter |

---

## 快速开始

### 环境要求

- Python 3.10+
- pip

### 安装与运行

```bash
# 1. 进入项目目录
cd RBVC

# 2. 安装依赖
pip install -r requirements.txt

# 3. 初始化数据库（建表 + 种子数据）
python init_db.py

# 4. 启动服务器
python app.py
```

浏览器访问 **http://localhost:5000**

### 默认账号

| 用户名 | 密码 | 角色 |
|--------|------|------|
| `admin` | `admin123` | Admin（完全控制） |

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

| 角色 | 描述 |
|------|------|
| **Admin** 管理员 | 完全系统控制 — 管理用户、角色、文件，查看审计日志 |
| **Manager** 经理 | 用户和角色管理，所有文件操作，查看审计日志 |
| **Editor** 编辑者 | 完整文件 CRUD 操作，可查看用户列表 |
| **Contributor** 贡献者 | 文件上传和编辑，不允许删除 |
| **Viewer** 浏览者 | 只读文件访问 |
| **Auditor** 审计员 | 查看审计日志和文件 |

---

## 项目结构

```
RBVC/
├── app.py                    # Flask 应用工厂 + 入口
├── config.py                 # 配置类（开发/生产）
├── extensions.py             # SQLAlchemy 共享实例
├── init_db.py                # 数据库初始化 + 种子数据
├── requirements.txt          # Python 依赖
│
├── models/                   # 数据模型
│   ├── user.py               # 用户（含 has_permission 方法）
│   ├── role.py               # 角色
│   ├── permission.py         # 权限
│   ├── file_model.py         # 文件元数据
│   └── audit_log.py          # 审计日志
│
├── routes/                   # API 路由
│   ├── auth.py               # 认证（登录/注册/个人信息）
│   ├── users.py              # 用户 CRUD
│   ├── roles.py              # 角色 CRUD + 权限分配
│   ├── permissions.py        # 权限列表
│   ├── files.py              # 文件 CRUD + 上传/下载
│   └── audit.py              # 审计日志查询
│
├── services/                 # 业务逻辑层
│   ├── auth_service.py       # 认证逻辑
│   ├── user_service.py       # 用户管理
│   ├── role_service.py       # 角色管理
│   ├── file_service.py       # 文件操作（UUID 安全存储）
│   └── audit_service.py      # 日志读写
│
├── middleware/
│   └── permissions.py        # require_permission 装饰器 + JWT 解码
│
├── utils/
│   ├── security.py           # 密码哈希 + JWT 编解码
│   └── validators.py         # 输入验证（用户名/密码/文件类型）
│
├── templates/                # Jinja2 前端页面
│   ├── base.html             # Bootstrap 5 基础布局
│   ├── login.html            # 登录页
│   ├── register.html         # 注册页
│   ├── dashboard.html        # 仪表盘
│   ├── users.html            # 用户管理
│   ├── roles.html            # 角色管理 + 权限矩阵
│   ├── files.html            # 文件管理器
│   └── audit.html            # 审计日志查看器
│
├── static/
│   ├── css/style.css         # 自定义样式
│   └── js/
│       ├── api.js            # 统一 fetch 封装（JWT 管理）
│       ├── auth.js           # 登录/注册逻辑
│       ├── dashboard.js      # 仪表盘统计
│       ├── users.js          # 用户管理逻辑
│       ├── roles.js          # 角色 + 权限矩阵逻辑
│       ├── files.js          # 文件上传/下载/删除逻辑
│       └── audit.js          # 审计日志筛选/分页
│
└── uploads/                  # 文件存储目录（UUID 命名）
```

---

## API 概览

所有 API 端点位于 `/api` 前缀下。除登录/注册外，均需 `Authorization: Bearer <token>` 头。

### 认证
| 方法 | 端点 | 认证 | 说明 |
|------|------|:----:|------|
| POST | `/api/auth/register` | — | 注册新用户 |
| POST | `/api/auth/login` | — | 登录获取 JWT |
| GET | `/api/auth/profile` | JWT | 当前用户信息 |

### 用户管理
| 方法 | 端点 | 权限 | 说明 |
|------|------|------|------|
| GET | `/api/users` | user:read | 用户列表 |
| POST | `/api/users` | user:create | 创建用户 |
| GET | `/api/users/<id>` | user:read | 用户详情 |
| PUT | `/api/users/<id>` | user:update | 编辑用户 |
| DELETE | `/api/users/<id>` | user:delete | 删除用户 |

### 角色管理
| 方法 | 端点 | 权限 |
|------|------|------|
| GET | `/api/roles` | role:read |
| POST | `/api/roles` | role:create |
| GET | `/api/roles/<id>` | role:read |
| PUT | `/api/roles/<id>` | role:update |
| DELETE | `/api/roles/<id>` | role:delete |
| GET | `/api/roles/<id>/permissions` | role:read |
| PUT | `/api/roles/<id>/permissions` | role:update |

### 文件管理
| 方法 | 端点 | 权限 | 说明 |
|------|------|------|------|
| GET | `/api/files` | file:read | 文件列表 |
| POST | `/api/files` | file:create | 上传（multipart） |
| GET | `/api/files/<id>` | file:read | 下载文件 |
| PUT | `/api/files/<id>` | file:update | 替换文件 |
| DELETE | `/api/files/<id>` | file:delete | 删除文件 |

### 审计日志
| 方法 | 端点 | 权限 | 参数 |
|------|------|------|------|
| GET | `/api/audit-logs` | audit:read | `?user_id=&action=&resource_type=&start_date=&end_date=&page=&per_page=` |

---

## 安全设计

| 安全项 | 实现方式 |
|--------|----------|
| 密码存储 | `werkzeug.security.generate_password_hash()` (bcrypt) |
| 身份认证 | JWT HS256 签名，24 小时过期，payload 含 user_id/username/roles/permissions |
| 权限校验 | `@require_permission(perm_name)` 装饰器，拒绝时记录审计日志 |
| SQL 注入防护 | SQLAlchemy ORM 参数化查询，全程无原始 SQL |
| 路径遍历防护 | `werkzeug.secure_filename()` + UUID 重命名 + `os.path.realpath()` 边界检查 |
| 文件上传安全 | 扩展名白名单（13 种），最大 16MB，服务端 MIME 验证 |
| XSS 防护 | Jinja2 自动 HTML 转义 + CSP 头 |
| CSRF 防护 | JWT 在 Authorization 头中（非 Cookie），天然免疫 CSRF |
| 登录限流 | Flask-Limiter，`/api/auth/login` 5 次/分钟/IP |
| 审计追踪 | 所有操作（含权限拒绝）记录到不可删除的 audit_logs 表 |

---

## 许可

本项目为北京科技大学 2026 年春季《软件安全实验》课程作业，仅供学习参考。
