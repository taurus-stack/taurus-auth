# Taurus Auth

<div align="center">

**安全的一次性票据认证服务**

[English](README.md) | [中文](README.zh-CN.md)

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python Version](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![Django Version](https://img.shields.io/badge/django-4.2+-green.svg)](https://www.djangoproject.com/)

</div>

## 📖 简介

Taurus Auth 是 Taurus 分布式运维管理系统的票据认证服务，提供安全的一次性票据生成、验证和管理功能。基于 Macaroon 令牌和 JWT 认证，确保命令执行的安全性和可追溯性。

### 核心特性

- 🔐 **票据认证**：基于 Macaroon 的一次性使用票据
- 🔑 **JWT 认证**：HMAC-SHA256 签名的服务间认证
- 🛡️ **多层安全**：IP 白名单 + 请求限流 + JWT 验证
- 📝 **审计日志**：完整的票据操作追踪
- 🚀 **高性能**：Redis 缓存支持
- 🔄 **票据管理**：生成、验证、撤销、查询

## 🚀 快速开始

### 环境要求

- Python 3.10+
- MySQL/MariaDB
- Redis
- Poetry

### 安装

```bash
# 克隆项目
git clone https://github.com/taurus-stack/taurus-auth.git
cd taurus-auth

# 安装依赖
poetry install

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，配置数据库和其他设置

# 数据库迁移
poetry run python manage.py migrate

# 启动服务
poetry run python manage.py runserver 0.0.0.0:8001
```

### 配置说明

主要环境变量：

```bash
# 数据库配置
DB_NAME=taurus_auth
DB_USER=root
DB_PASSWORD=your-password
DB_HOST=localhost
DB_PORT=3306

# Redis 配置
REDIS_URL=redis://127.0.0.1:6379/1

# JWT 配置
BACKEND_JWT_SECRET=your-jwt-secret-key
BACKEND_JWT_EXPIRES_MINUTES=60

# 安全配置
ALLOWED_BACKEND_IPS=127.0.0.1,your-backend.local
ALLOWED_BACKEND_SERVICES=taurus-backend
RATELIMIT_ENABLE=True
RATELIMIT_RATE=100/m

# Macaroon 配置
MACAROON_ROOT_KEY=your-macaroon-root-key
```

## 📚 API 文档

### 健康检查

```bash
GET /health/
```

### 生成票据

```bash
POST /api/v1/tickets/generate
Authorization: Bearer <jwt-token>

{
  "host_uuid": "550e8400-e29b-41d4-a716-446655440000",
  "action": "execute_command",
  "command": "ls -la",
  "expires_minutes": 5
}
```

### 验证票据

```bash
POST /api/v1/tickets/verify

{
  "ticket": "MDAxMmxvY2F0aW9uIHRhdXJ1cy1hdXRo...",
  "client_ip": "192.168.1.100"
}
```

### 撤销票据

```bash
POST /api/v1/tickets/{ticket_id}/revoke
Authorization: Bearer <jwt-token>
```

### 查询票据列表

```bash
GET /api/v1/tickets/list?host_uuid={host_uuid}&status={status}
Authorization: Bearer <jwt-token>
```

### 审计日志

```bash
GET /api/v1/tickets/audit-logs?ticket_id={ticket_id}
Authorization: Bearer <jwt-token>
```

## 🏗️ 架构设计

### 三层安全模型

```
┌─────────────────────────────────────────┐
│         请求到达 taurus-auth             │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  第一层：IP 白名单检查                   │
│  - 检查客户端 IP 是否在白名单中          │
│  - 不在白名单 → 403 Forbidden           │
└──────────────┬──────────────────────────┘
               │ 通过
               ▼
┌─────────────────────────────────────────┐
│  第二层：请求限流                        │
│  - 检查请求频率是否超过限制              │
│  - 超过限制 → 429 Too Many Requests     │
└──────────────┬──────────────────────────┘
               │ 通过
               ▼
┌─────────────────────────────────────────┐
│  第三层：JWT Token 验证                  │
│  - 验证 Token 签名、过期时间             │
│  - 检查服务标识是否在允许列表中          │
│  - 验证失败 → 401 Unauthorized          │
└──────────────┬──────────────────────────┘
               │ 通过
               ▼
┌─────────────────────────────────────────┐
│  执行业务逻辑（生成/撤销/查询票据）      │
└─────────────────────────────────────────┘
```

### 项目结构

```
taurus-auth/
├── taurus_auth/          # Django 项目配置
│   ├── settings.py       # 项目设置
│   ├── urls.py           # 主路由
│   ├── wsgi.py           # WSGI 配置
│   └── asgi.py           # ASGI 配置
├── ticket/               # 票据认证应用
│   ├── models.py         # 数据模型
│   ├── views.py          # API 视图
│   ├── serializers.py    # 序列化器
│   ├── services.py       # 业务逻辑
│   ├── middleware.py     # 安全中间件
│   ├── urls.py           # 应用路由
│   └── utils/            # 工具类
│       └── jwt_helper.py # JWT 工具
├── db/                   # 数据库脚本
│   ├── dump_export_auth.sh
│   └── dump_import_auth.sh
├── manage.py             # Django 管理脚本
├── pyproject.toml        # Poetry 配置
└── test_jwt_auth.py      # JWT 测试
```

## 🔒 安全特性

| 特性 | 说明 |
|------|------|
| JWT 认证 | HMAC-SHA256 签名，自动过期 |
| IP 白名单 | 限制特定 IP 访问 |
| 请求限流 | 防止暴力攻击 |
| Macaroon 票据 | 一次性使用，加密验证 |
| Nonce 追踪 | 防止重放攻击 |
| 审计日志 | 完整操作记录 |

## 🧪 测试

```bash
# 运行所有测试
poetry run pytest

# 运行覆盖率测试
poetry run pytest --cov=ticket

# 运行 JWT 认证测试
poetry run pytest test_jwt_auth.py
```

## 📦 部署

### 生产环境配置

1. **使用强随机密钥**：
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

2. **限制 IP 白名单**：
   ```bash
   ALLOWED_BACKEND_IPS=10.0.0.0/24,172.16.0.0/16
   ```

3. **启用 HTTPS**：
   ```nginx
   server {
       listen 443 ssl;
       server_name auth.taurus.example.com;
       
       ssl_certificate /path/to/cert.pem;
       ssl_certificate_key /path/to/key.pem;
       
       location / {
           proxy_pass http://127.0.0.1:8001;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

### Docker 部署

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# 安装 Poetry
RUN pip install poetry

# 复制依赖文件
COPY pyproject.toml poetry.lock ./

# 安装依赖
RUN poetry config virtualenvs.create false \
    && poetry install --no-dev --no-interaction --no-ansi

# 复制应用代码
COPY . .

# 运行迁移
RUN python manage.py migrate --noinput

# 暴露端口
EXPOSE 8001

# 启动服务
CMD ["gunicorn", "taurus_auth.wsgi:application", "--bind", "0.0.0.0:8001"]
```

## 📝 配置参考

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `DB_ENGINE` | 数据库引擎 | `django.db.backends.mysql` |
| `DB_NAME` | 数据库名称 | `taurus_auth` |
| `DB_USER` | 数据库用户 | `root` |
| `DB_PASSWORD` | 数据库密码 | - |
| `DB_HOST` | 数据库主机 | `localhost` |
| `DB_PORT` | 数据库端口 | `3306` |
| `REDIS_URL` | Redis URL | `redis://127.0.0.1:6379/1` |
| `BACKEND_JWT_SECRET` | JWT 签名密钥 | - |
| `BACKEND_JWT_EXPIRES_MINUTES` | JWT 过期时间（分钟） | `60` |
| `ALLOWED_BACKEND_IPS` | 允许的后端 IP | - |
| `ALLOWED_BACKEND_SERVICES` | 允许的服务标识 | `taurus-backend` |
| `RATELIMIT_ENABLE` | 启用限流 | `True` |
| `RATELIMIT_RATE` | 限流速率 | `100/m` |
| `MACAROON_ROOT_KEY` | Macaroon 根密钥 | - |
| `TICKET_DEFAULT_EXPIRES_MINUTES` | 默认票据过期时间 | `5` |
| `TICKET_MAX_EXPIRES_MINUTES` | 最大票据过期时间 | `60` |

## 🤝 贡献指南

欢迎贡献！请参阅 [CONTRIBUTING.md](CONTRIBUTING.md) 了解详细信息。

## 📄 许可证

本项目基于 GNU Affero General Public License v3.0 发布 - 详见 [LICENSE](LICENSE) 文件。

## 🔗 相关链接

- [Taurus Backend](https://github.com/taurus-stack/taurus-backend) - 后端 API 服务
- [Taurus Web](https://github.com/taurus-stack/taurus-web) - 前端管理界面
- [Taurus Executor](https://github.com/taurus-stack/taurus-executor) - 客户端执行器
- [Taurus Supervisor](https://github.com/taurus-stack/taurus-supervisor) - 主机守护进程

## 📧 联系方式

- 问题反馈：[GitHub Issues](https://github.com/taurus-stack/taurus-auth/issues)
- 讨论区：[GitHub Discussions](https://github.com/taurus-stack/taurus-auth/discussions)
- 安全漏洞：[SECURITY.md](SECURITY.md)
