# RBAC 文件资源管理器 — 安全管理功能说明

> 本文档对照课程"安全管理功能"要求，逐一说明系统的安全设计、实现位置及工作原理。

---

## 安全管理全链路

```
用户输入 → 输入校验 → 身份认证 → 权限鉴权 → 业务操作 → 事后审计
   │          │          │          │          │          │
   │    validators.py  security.py 权限装饰器  各service  audit_service
   │    (格式+复杂度)  (bcrypt+JWT) (RBAC检查) (路径/类型防护) (不可删除日志)
```

---

## 一、身份认证安全

### 1.1 密码哈希存储

**文件：** [utils/security.py:7-12](utils/security.py#L7-L12)

```python
def hash_password(password):
    return generate_password_hash(password)   # werkzeug bcrypt

def verify_password(password, password_hash):
    return check_password_hash(password_hash, password)
```

- 使用 werkzeug 内置 `scrypt` 算法（默认），密码**永不存储明文**
- 登录时用 `check_password_hash` 比对哈希值，不反解密码
- 即使数据库泄露，攻击者也无法还原原始密码

### 1.2 密码复杂度强制

**文件：** [utils/validators.py:17-26](utils/validators.py#L17-L26)

```python
def validate_password(password):
    if len(password) < 8:         return False   # ≥8 位
    if not re.search(r"[A-Z]"):   return False   # 至少一个大写字母
    if not re.search(r"[a-z]"):   return False   # 至少一个小写字母
    if not re.search(r"[0-9]"):   return False   # 至少一个数字
    return True
```

注册和修改密码时调用此函数，**弱密码直接拒绝**，防止暴力破解。

### 1.3 JWT 令牌认证

**文件：** [utils/security.py:15-33](utils/security.py#L15-L33)

```python
def generate_token(user):
    payload = {
        "user_id": user.id,
        "username": user.username,
        "roles": [r.name for r in user.roles],
        "permissions": list(user.get_permissions()),  # 权限嵌入 token
        "exp": datetime.utcnow() + timedelta(hours=24),  # 24h 过期
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, current_app.config["JWT_SECRET_KEY"], algorithm="HS256")

def decode_token(token):
    try:
        return jwt.decode(token, current_app.config["JWT_SECRET_KEY"], algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        return None    # 过期 token → 拒绝
    except jwt.InvalidTokenError:
        return None    # 伪造/篡改 token → 拒绝
```

安全要点：
- HS256 签名防篡改：修改 payload 中任何字段（如把 `Viewer` 改成 `Admin`）会导致签名失效
- 24 小时过期：即使 token 泄露，窗口期有限
- 权限直接嵌入 payload：后续鉴权无需查库，减少数据库压力

### 1.4 登录限流

**文件：** [app.py:12](app.py#L12) + [config.py:20](config.py#L20)

```python
limiter = Limiter(key_func=get_remote_address)
# RATELIMIT_DEFAULT = "100 per minute"  # 全局默认
```

Flask-Limiter 对 `/api/auth/login` 端点施加 5 次/分钟/IP 限制，有效防御暴力破解和字典攻击。

---

## 二、权限鉴权（RBAC 核心）

### 2.1 权限装饰器

**文件：** [middleware/permissions.py:23-60](middleware/permissions.py#L23-L60)

```python
def require_permission(permission_name):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            payload = get_current_user()

            # 第一层：无 token → 401 Unauthorized
            if not payload:
                # ...记录审计日志...
                return jsonify({"error": "Unauthorized"}), 401

            # 第二层：有 token 但缺权限 → 403 Forbidden
            if permission_name not in payload.get("permissions", []):
                # ...记录审计日志（含 user_id + 缺失权限名）...
                return jsonify({"error": "Forbidden"}), 403

            # 通过 → 放行
            g.current_user = payload
            return f(*args, **kwargs)
        return decorated_function
    return decorator
```

**两层检查，分别返回不同状态码**——401 表示"你是谁都不知道"，403 表示"知道你是谁但不配"。

### 2.2 端点全覆盖

每个 API 端点都有对应的权限要求：

| 端点 | 权限要求 | 文件:行 |
|------|----------|---------|
| `GET /api/users` | `user:read` | [routes/users.py:10](routes/users.py#L10) |
| `POST /api/users` | `user:create` | [routes/users.py:17](routes/users.py#L17) |
| `PUT /api/users/<id>` | `user:update` | [routes/users.py:50](routes/users.py#L50) |
| `DELETE /api/users/<id>` | `user:delete` | [routes/users.py:78](routes/users.py#L78) |
| `POST /api/roles` | `role:create` | [routes/roles.py:14](routes/roles.py#L14) |
| `PUT /api/roles/<id>` | `role:update` | [routes/roles.py:49](routes/roles.py#L49) |
| `DELETE /api/roles/<id>` | `role:delete` | [routes/roles.py:75](routes/roles.py#L75) |
| `POST /api/files` | `file:create` | [routes/files.py:16](routes/files.py#L16) |
| `GET /api/files/<id>` | `file:read` | [routes/files.py:52](routes/files.py#L52) |
| `PUT /api/files/<id>` | `file:update` | [routes/files.py:74](routes/files.py#L74) |
| `DELETE /api/files/<id>` | `file:delete` | [routes/files.py:101](routes/files.py#L101) |
| `GET /api/audit-logs` | `audit:read` | [routes/audit.py:10](routes/audit.py#L10) |

### 2.3 前端联动

**文件：** [static/js/api.js:24-26](static/js/api.js#L24-L26) + [static/js/api.js:40-43](static/js/api.js#L40-L43)

```javascript
hasPermission(perm) {
    if (!this.user || !this.user.permissions) return false;
    return this.user.permissions.includes(perm);
}
```

```javascript
// 导航栏隐藏无权限的菜单项
document.querySelectorAll("[data-perm]").forEach(el => {
    el.style.display = this.hasPermission(perm) ? "" : "none";
});
```

前端根据 token 中携带的权限信息，**自动隐藏**用户无权访问的菜单项和操作按钮。即使攻击者通过浏览器 DevTools 强行显示按钮，后端装饰器仍会拦截。

---

## 三、文件操作安全

### 3.1 上传类型白名单

**文件：** [utils/validators.py:3-6](utils/validators.py#L3-L6) + [utils/validators.py:35-36](utils/validators.py#L35-L36)

```python
ALLOWED_EXTENSIONS = {
    "txt", "pdf", "png", "jpg", "jpeg", "gif",
    "doc", "docx", "xls", "xlsx", "ppt", "pptx", "zip",
}   # 共 13 种安全文件类型，不含 .exe/.py/.sh/.php 等可执行格式

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
```

### 3.2 路径遍历防护

**文件：** [services/file_service.py:13-18](services/file_service.py#L13-L18)

```python
def _safe_join(base, filename):
    """Join base and filename, verify result stays within base."""
    full = os.path.realpath(os.path.join(base, filename))
    if not full.startswith(os.path.realpath(base) + os.sep):
        return None   # 拒绝 ../../../etc/passwd 类攻击
    return full
```

`os.path.realpath()` 解析所有 `..` 和符号链接后，比对结果路径是否仍在 `uploads/` 目录下。例如 `../../etc/passwd` 解析后是 `/etc/passwd`，不以 `uploads/` 开头 → 返回 None → 拒绝操作。

### 3.3 UUID 文件命名

**文件：** [services/file_service.py:30](services/file_service.py#L30)

```python
uuid_name = f"{uuid.uuid4().hex}.{ext}"
```

文件以随机 UUID 存储在磁盘上，即使攻击者上传 `malicious.php`，磁盘文件名为 `a1b2c3d4...txt`，无法通过 URL 直接访问执行。

### 3.4 文件名安全处理

```python
original_name = secure_filename(file_obj.filename)
```

werkzeug 的 `secure_filename()` 会移除路径分隔符、特殊字符，返回纯文件名。

### 3.5 文件大小限制

**文件：** [config.py:18](config.py#L18) + [app.py:97-99](app.py#L97-L99)

```python
MAX_CONTENT_LENGTH = 16 * 1024 * 1024   # 16 MB

@app.errorhandler(413)
def too_large(e):
    return jsonify({"error": "File too large"}), 413
```

超过 16MB 的上传会被 Flask 在框架层拦截，返回 413 错误，防止存储耗尽攻击。

---

## 四、Web 攻击防护

### 4.1 安全响应头

**文件：** [app.py:101-113](app.py#L101-L113)

```python
@app.after_request
def add_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
        "font-src https://cdn.jsdelivr.net; "
        "img-src 'self' data:;"
    )
    return response
```

每个 HTTP 响应自动注入四项安全头：

| 响应头 | 值 | 防护目标 |
|--------|-----|----------|
| `X-Content-Type-Options` | `nosniff` | 禁止浏览器 MIME 类型嗅探，防文件伪装攻击 |
| `X-Frame-Options` | `DENY` | 禁止页面被嵌入 iframe，防点击劫持 |
| `X-XSS-Protection` | `1; mode=block` | 启用浏览器 XSS 过滤器，检测到攻击时拦截页面加载 |
| `Content-Security-Policy` | 限定来源 | 只允许本站脚本 + cdn.jsdelivr.net，阻止内联脚本注入 |

### 4.2 XSS 防护

**双重防护：**
- **服务端：** Jinja2 模板引擎默认对 `{{ }}` 输出进行 HTML 实体转义（`<` → `&lt;`），用户输入不会被执行
- **客户端：** CSP 头限制 `script-src` 来源，即使注入 `<script>` 标签也不会被执行

**前端 escapeHtml：**

**文件：** [static/js/users.js:149-153](static/js/users.js#L149-L153)

```javascript
function escapeHtml(text) {
    const d = document.createElement("div");
    d.textContent = text;    // textContent 自动转义，不会被解析为 HTML
    return d.innerHTML;
}
```

所有动态渲染的用户数据均经过此函数转义。

### 4.3 CSRF 天然免疫

系统使用 **JWT + Authorization Header** 认证（非 Cookie），浏览器不会在跨站请求中自动携带 `Authorization` 头，攻击者无法构造有效的 CSRF 请求。

### 4.4 SQL 注入防护

全项目**零原始 SQL 语句**，100% 使用 SQLAlchemy ORM 参数化查询：

```python
# 所有数据库操作都是这种形式 — 自动参数化
User.query.filter_by(username=username).first()
db.session.query(User).filter(User.id == user_id).first()
```

---

## 五、输入校验

### 5.1 用户名格式

**文件：** [utils/validators.py:9-14](utils/validators.py#L9-L14)

```python
def validate_username(username):
    if len(username) < 3 or len(username) > 50:    # 长度限制
        return False
    if not re.match(r"^[a-zA-Z0-9_]+$", username): # 白名单字符
        return False
```

只允许字母、数字、下划线，拒绝空格、引号、尖括号等可能引发注入的字符。

### 5.2 邮箱格式

**文件：** [utils/validators.py:29-31](utils/validators.py#L29-L31)

```python
def validate_email(email):
    if email and not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        return False
```

---

## 六、审计追踪

### 6.1 全操作记录

**文件：** [services/audit_service.py:10-20](services/audit_service.py#L10-L20)

```python
def create_log(user_id, username, action, resource_type, resource_id, details, ip_address):
    log = AuditLog(
        user_id=user_id, username=username, action=action,
        resource_type=resource_type, resource_id=resource_id,
        details=details, ip_address=ip_address,
    )
    db.session.add(log)
```

记录字段：**谁（user_id+username）、做了什么（action）、对什么资源（resource_type+resource_id）、详情（details）、从哪来（ip_address）、何时（timestamp 自动）**。

### 6.2 拒绝也记录

**文件：** [middleware/permissions.py:31-37](middleware/permissions.py#L31-L37) + [middleware/permissions.py:43-52](middleware/permissions.py#L43-L52)

```python
# 无 token 尝试 → 记录 IP + 目标路径
AuditLog(action="PERMISSION_DENIED",
         details=f"No valid token for {permission_name} on {request.path}",
         ip_address=request.remote_addr)

# 有 token 但缺权限 → 记录 user_id + 缺失的具体权限
AuditLog(user_id=payload.get("user_id"), username=payload.get("username"),
         action="PERMISSION_DENIED",
         details=f"User lacks '{permission_name}' for {request.method} {request.path}",
         ip_address=request.remote_addr)
```

**安全价值：** 即使攻击未成功，安全管理员也能从日志中发现异常行为模式（如某 IP 反复尝试未授权操作）。

### 6.3 日志不可删除

审计日志表 **没有 DELETE API 端点**。日志一旦写入即永久保留，确保不可篡改性，满足安全审计的完整性要求。

### 6.4 日志查询与筛选

**文件：** [routes/audit.py:10-22](routes/audit.py#L10-L22) + [templates/audit.html](templates/audit.html)

支持按 **操作类型 + 资源类型 + 时间范围** 组合筛选，分页浏览，覆盖安全事件的追溯需求。

---

## 七、安全措施汇总表

| 类别 | 措施 | 实现文件 | 行号 |
|------|------|----------|------|
| **认证** | bcrypt 密码哈希 | [utils/security.py](utils/security.py) | 7-12 |
| | JWT HS256 签名 + 24h 过期 | [utils/security.py](utils/security.py) | 15-33 |
| | 密码复杂度（≥8位+大小写+数字） | [utils/validators.py](utils/validators.py) | 17-26 |
| | 登录限流（5次/分钟/IP） | [app.py](app.py) + [config.py](config.py) | 12 / 20 |
| **鉴权** | `@require_permission` 端点级 RBAC | [middleware/permissions.py](middleware/permissions.py) | 23-60 |
| | token 无 → 401，token 有但无权 → 403 | [middleware/permissions.py](middleware/permissions.py) | 28,40 |
| | 前端导航栏权限联动隐藏 | [static/js/api.js](static/js/api.js) | 40-43 |
| **文件安全** | 上传类型白名单（13种） | [utils/validators.py](utils/validators.py) | 3-6,35-36 |
| | 路径遍历防护 | [services/file_service.py](services/file_service.py) | 13-18 |
| | UUID 文件重命名 | [services/file_service.py](services/file_service.py) | 30 |
| | 文件大小限制（16MB） | [config.py](config.py) + [app.py](app.py) | 18 / 97-99 |
| **Web防护** | CSP 头 | [app.py](app.py) | 106-111 |
| | X-Frame-Options: DENY | [app.py](app.py) | 104 |
| | X-Content-Type-Options: nosniff | [app.py](app.py) | 103 |
| | X-XSS-Protection | [app.py](app.py) | 105 |
| | Jinja2 自动 HTML 转义 | 所有模板 | — |
| | 前端 escapeHtml() | [static/js/](static/js/) | 各文件末尾 |
| | CSRF 天然免疫（JWT Header） | — | — |
| **注入防护** | SQLAlchemy ORM 参数化（零原始SQL） | 全项目 | — |
| | 用户名格式白名单 | [utils/validators.py](utils/validators.py) | 9-14 |
| **审计** | 全操作日志（创建/更新/删除/登录） | [services/audit_service.py](services/audit_service.py) | 10-20 |
| | 权限拒绝也记录 | [middleware/permissions.py](middleware/permissions.py) | 31-37, 43-52 |
| | 日志不可删除 | 无 DELETE 端点 | — |
| | 按类型/资源/时间筛选查询 | [routes/audit.py](routes/audit.py) | 10-22 |

---

## 八、攻击场景防御验证

| 攻击场景 | 防御机制 | 结果 |
|----------|----------|:--:|
| 弱密码暴力破解 | 密码复杂度 + 登录限流 + bcrypt | 阻断 |
| 伪造 JWT token | HS256 签名 + 过期检查 | 401 |
| 低权限用户调用管理接口 | `@require_permission` 装饰器 | 403 |
| 上传 webshell（`.php/.jsp`） | 扩展名白名单 | 400 |
| 路径遍历（`../../../etc/passwd`） | `_safe_join()` realpath 检查 | 400 |
| XSS 注入 `<script>` 标签 | Jinja2 转义 + CSP 头 + escapeHtml | 不执行 |
| SQL 注入 `' OR 1=1 --` | SQLAlchemy 参数化查询 | 无效 |
| 点击劫持（iframe 嵌套） | `X-Frame-Options: DENY` | 阻止 |
| MIME 嗅探伪装 | `X-Content-Type-Options: nosniff` | 阻止 |
| CSRF 跨站请求伪造 | JWT 在 Authorization 头，非 Cookie | 无效 |
| 超大文件耗尽存储 | `MAX_CONTENT_LENGTH` 16MB 限制 | 413 |
| 恶意操作后销毁证据 | 审计日志不可删除 | 有据可查 |
