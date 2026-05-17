# KeyPool

API Key 池代理服务。为 Tavily、Context7、Exa 等平台提供多密钥加权轮询，通过中间代理实现额度扩展。

支持 MCP（Streamable HTTP）和 REST API 双协议代理，用户只需将上游 URL 替换为 KeyPool 部署地址，即可透明使用多 Key 轮询能力。

## 特性

- **多 Key 加权轮询** — 根据基础权重、错误率、剩余额度动态计算有效权重
- **MCP + REST 双协议代理** — 同时代理 Streamable HTTP (MCP) 和平台 REST API
- **HTTP/2 连接复用** — 共享连接池 + HTTP/2 多路复用，最小化延迟
- **透明透传** — 不解析协议内容，请求体/响应体/状态码完全透传
- **智能计数** — 仅对实际使用（REST 请求、MCP tools/call）计数，协议握手不计
- **Session 绑定** — 长连接期间始终使用同一个 Key，避免上下文切换
- **出口代理池** — 支持 HTTP/HTTPS/SOCKS5 出口代理，失败自动换代理重试
- **Key 状态自动流转** — 根据上游响应码自动标记 Key 为耗尽或失效
- **定时额度刷新** — 事件驱动 + 延迟刷新，只有被使用的 Key 才触发额度查询
- **双层认证** — Admin Key 管理接口 + 项目 Token 代理接口，权限隔离
- **插件式架构** — 每个平台独立目录，新增/删除平台零耦合
- **Web 管理面板** — Vue 3 前端，Apple 风格 UI

## 快速开始

### 1. 配置

复制配置样例并修改：

```bash
cp config.example.json config.json
```

编辑 `config.json`，设置 `admin_key` 和启用的平台：

```json
{
  "host": "0.0.0.0",
  "port": 8000,
  "admin_key": "your-secret-key",
  "database": "data/keypool.db",
  "retry_limit": 3,
  "platforms": {
    "tavily": {"enabled": true, "upstream_base_url": "https://mcp.tavily.com"},
    "context7": {"enabled": true, "upstream_base_url": "https://mcp.context7.com"},
    "exa": {"enabled": true, "upstream_base_url": "https://api.exa.ai"}
  }
}
```

### 2. 部署

#### Docker Compose（本地构建）

```bash
docker compose -f docker-compose.build.yml up -d
```

#### Docker Compose（使用预构建镜像）

```bash
docker compose up -d
```

#### 本地开发

```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 3. 使用

1. 通过管理面板或 API 导入 Key：

```bash
curl -X POST http://localhost:8000/admin/keys \
  -H "Authorization: Bearer your-secret-key" \
  -H "Content-Type: application/json" \
  -d '{"platform": "tavily", "api_key": "tvly-xxx"}'
```

2. 创建项目 Token：

```bash
curl -X POST http://localhost:8000/admin/tokens \
  -H "Authorization: Bearer your-secret-key" \
  -H "Content-Type: application/json" \
  -d '{"name": "my-token", "allowed_platforms": ["tavily", "context7", "exa"]}'
```

3. 将 MCP 客户端配置指向 KeyPool：

```json
{
  "mcpServers": {
    "tavily-remote-mcp": {
      "command": "npx -y mcp-remote http://your-keypool:8000/api/tavily/mcp?token=<project_token>"
    }
  }
}
```

4. REST API 直接调用（与原始 API 完全兼容）：

```bash
# Tavily 搜索
curl -X POST http://your-keypool:8000/api/tavily/search \
  -H "Authorization: Bearer <project_token>" \
  -H "Content-Type: application/json" \
  -d '{"query": "latest AI news", "max_results": 5}'

# Context7 文档查询
curl -X POST http://your-keypool:8000/api/context7/api/v2/context \
  -H "Authorization: Bearer <project_token>" \
  -H "Content-Type: application/json" \
  -d '{"libraryId": "/vercel/next.js", "query": "app router"}'

# Exa 搜索
curl -X POST http://your-keypool:8000/api/exa/search \
  -H "Authorization: Bearer <project_token>" \
  -H "Content-Type: application/json" \
  -d '{"query": "machine learning papers", "num_results": 10}'
```

## 架构概览

```
客户端 → 鉴权中间件 → 平台插件路由(resolve_upstream) → 核心框架层(Key选择/代理选择/Session管理) → 代理引擎(HTTP/2透传) → 上游服务
```

### 目录结构

```
KeyPool/
├── app/
│   ├── main.py              # FastAPI 入口
│   ├── config.py            # 配置加载
│   ├── core/                # 核心框架层
│   │   ├── key_selector.py  # 加权轮询选 Key
│   │   ├── proxy_selector.py# 出口代理轮询
│   │   ├── session_manager.py
│   │   ├── auth.py          # 双层认证
│   │   └── models.py        # ORM 模型
│   ├── proxy/               # 代理引擎层
│   │   ├── sse_proxy.py     # SSE 透传
│   │   ├── http_proxy.py    # HTTP 转发
│   │   └── client.py        # 出口 HTTP 客户端
│   ├── platforms/           # 平台插件
│   │   ├── base.py          # 插件基类
│   │   ├── tavily/
│   │   ├── context7/
│   │   └── exa/
│   └── api/                 # 管理接口
├── web/                     # Vue 3 前端
├── config.example.json
├── docker-compose.yml       # 本地构建
├── docker-compose.ghcr.yml  # 预构建镜像
└── Dockerfile
```

## 支持的平台

| 平台 | Key 注入方式 | 额度查询 | 协议 |
|------|-------------|---------|------|
| Tavily | URL param / Bearer Header | 支持 | Streamable HTTP + REST |
| Context7 | `CONTEXT7_API_KEY` / Bearer Header | 不支持 | Streamable HTTP + REST |
| Exa | `x-api-key` / Bearer Header | 不支持 | Streamable HTTP + REST |

### REST API 路由规则

`/api/{platform}/{path}` 中的 path 直接拼接到平台上游地址：

| KeyPool 路径 | 上游地址 |
|---|---|
| `/api/tavily/mcp` | `https://mcp.tavily.com/mcp` |
| `/api/tavily/search` | `https://api.tavily.com/search` |
| `/api/context7/mcp` | `https://mcp.context7.com/mcp` |
| `/api/context7/api/v2/context` | `https://context7.com/api/v2/context` |
| `/api/exa/mcp` | `https://mcp.exa.ai/mcp` |
| `/api/exa/search` | `https://api.exa.ai/search` |

### 新增平台

1. 创建 `app/platforms/{name}/plugin.py`，实现 `PlatformPlugin` 基类
2. 在 `app/platforms/__init__.py` 注册
3. 在 `config.json` 添加平台配置

## API 文档

详见 [doc/api.md](doc/api.md)。

## 技术栈

| 层级 | 选型 |
|------|------|
| Web 框架 | FastAPI + Uvicorn |
| 数据库 | SQLite + SQLAlchemy |
| HTTP 客户端 | httpx（HTTP/2 + 连接池） |
| 前端 | Vue 3 + Vite + Pinia |
| 部署 | Docker + Docker Compose |

## License

[GNU](LICENSE)
