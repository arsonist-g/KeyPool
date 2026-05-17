# KeyPool API 文档

## 认证方式

### 管理接口（/admin/*）

使用 `config.json` 中的 `admin_key`，通过 Header 传递：

```
Authorization: Bearer <admin_key>
```

### 代理接口（/api/{platform}/mcp/*）

使用管理员分发的项目 Token，支持两种方式：

```
# Query Parameter
GET /api/tavily/mcp?token=<project_token>

# Header
Authorization: Bearer <project_token>
```

---

## 公开接口

### 健康检查

```
GET /health
```

响应：
```json
{"status": "ok"}
```

### 登录

```
POST /admin/auth/login
```

请求体：
```json
{"admin_key": "your-admin-key"}
```

响应：
```json
{"success": true, "token": "your-admin-key"}
```

---

## 管理接口

> 以下接口均需 Admin Key 认证

### Key 管理

#### 列出 Key

```
GET /admin/keys?platform=tavily&status=active&page=1&page_size=20
```

Query 参数（均可选）：
- `platform` — 按平台过滤
- `status` — 按状态过滤（active / disabled / exhausted）
- `page` — 页码，默认 1
- `page_size` — 每页数量，默认 20，最大 100

响应：
```json
{
  "items": [
    {
      "id": 1,
      "platform": "tavily",
      "api_key": "tvly-xxx",
      "weight": 1.0,
      "status": "active",
      "total_requests": 42,
      "failed_requests": 2,
      "last_used_at": "2025-05-18T10:00:00",
      "quota_remaining": 0.8,
      "quota_updated_at": "2025-05-18T09:30:00",
      "created_at": "2025-05-01T00:00:00"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20
}
```

#### 创建 Key

```
POST /admin/keys
```

请求体：
```json
{
  "platform": "tavily",
  "api_key": "tvly-xxx",
  "weight": 1.0
}
```

响应：`201` + KeyResponse

错误：`409` Key 已存在

#### 获取单个 Key

```
GET /admin/keys/{key_id}
```

#### 更新 Key

```
PATCH /admin/keys/{key_id}
```

请求体（字段均可选）：
```json
{
  "weight": 2.0,
  "status": "active"
}
```

#### 删除 Key

```
DELETE /admin/keys/{key_id}
```

响应：`204 No Content`

#### 查询 Key 额度

```
GET /admin/keys/{key_id}/quota
```

响应：
```json
{
  "supported": true,
  "remaining": 0.75,
  "raw": {},
  "error": null
}
```

---

### Token 管理

#### 列出 Token

```
GET /admin/tokens?page=1&page_size=20
```

响应：
```json
{
  "items": [
    {
      "id": 1,
      "name": "张三的token",
      "token_value": "a1b2c3...",
      "allowed_platforms": ["tavily", "context7"],
      "status": "active",
      "created_at": "2025-05-01T00:00:00"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20
}
```

#### 创建 Token

```
POST /admin/tokens
```

请求体：
```json
{
  "name": "张三的token",
  "allowed_platforms": ["tavily", "context7"]
}
```

响应：`201` + TokenResponse（token_value 自动生成）

错误：`409` 名称已存在

#### 获取单个 Token

```
GET /admin/tokens/{token_id}
```

#### 更新 Token

```
PATCH /admin/tokens/{token_id}
```

请求体（字段均可选）：
```json
{
  "name": "新名称",
  "allowed_platforms": ["tavily"],
  "status": "disabled"
}
```

#### 删除 Token

```
DELETE /admin/tokens/{token_id}
```

响应：`204 No Content`

---

### 代理池管理

#### 列出代理

```
GET /admin/proxies?page=1&page_size=20
```

响应：
```json
{
  "items": [
    {
      "id": 1,
      "protocol": "http",
      "host": "proxy.example.com",
      "port": 8080,
      "username": "user",
      "password": "pass",
      "status": "active",
      "created_at": "2025-05-01T00:00:00"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20
}
```

#### 创建代理

```
POST /admin/proxies
```

请求体：
```json
{
  "protocol": "http",
  "host": "proxy.example.com",
  "port": 8080,
  "username": "user",
  "password": "pass"
}
```

响应：`201` + ProxyResponse

错误：`409` 相同 host:port 已存在

#### 获取单个代理

```
GET /admin/proxies/{proxy_id}
```

#### 更新代理

```
PATCH /admin/proxies/{proxy_id}
```

请求体（字段均可选）：
```json
{
  "protocol": "socks5",
  "host": "new-proxy.example.com",
  "port": 1080,
  "username": "new-user",
  "password": "new-pass",
  "status": "disabled"
}
```

#### 删除代理

```
DELETE /admin/proxies/{proxy_id}
```

响应：`204 No Content`

---

### 统计接口

#### 全局统计

```
GET /admin/stats
```

响应：
```json
[
  {
    "platform": "tavily",
    "total_keys": 5,
    "active_keys": 4,
    "total_requests": 1200,
    "failed_requests": 30,
    "active_sessions": 2
  }
]
```

#### 额度概览

```
GET /admin/stats/quota/overview
```

响应：
```json
[
  {
    "platform": "tavily",
    "keys": [
      {"id": 1, "remaining": 0.8},
      {"id": 2, "remaining": 0.5}
    ],
    "avg_remaining": 0.65
  }
]
```

仅返回支持额度查询的平台。

#### 单平台统计

```
GET /admin/stats/{platform}
```

响应：同 PlatformStats 结构。

---

### 平台信息

```
GET /admin/platforms
```

响应：
```json
[
  {"name": "tavily", "enabled": true, "quota_supported": true},
  {"name": "context7", "enabled": true, "quota_supported": false},
  {"name": "exa", "enabled": true, "quota_supported": false}
]
```

---

## 代理接口

> 以下接口需项目 Token 认证

### Tavily

```
GET/POST /api/tavily/mcp?token=<project_token>
GET/POST /api/tavily/mcp/{path}?token=<project_token>
```

透传至 `https://mcp.tavily.com/mcp/{path}`，自动注入 Key。

### Context7

```
GET/POST /api/context7/mcp/{path}?token=<project_token>
```

透传至 `https://mcp.context7.com/mcp/{path}`，通过 `CONTEXT7_API_KEY` Header 注入 Key。

### Exa

```
GET/POST /api/exa/mcp/{path}?token=<project_token>
```

透传至 `https://mcp.exa.ai/mcp/{path}`，通过 `x-api-key` Header 注入 Key。

---

## 错误码

| 状态码 | 含义 |
|--------|------|
| 401 | 未认证或 Token 无效 |
| 403 | Token 无权访问该平台 |
| 404 | 资源不存在 |
| 409 | 资源冲突（重复创建） |
| 503 | 无可用 Key |
