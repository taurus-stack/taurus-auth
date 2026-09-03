# 变更日志

本项目的所有显著更改都将记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
并且本项目遵循 [语义化版本](https://semver.org/lang/zh-CN/spec/v2.0.0.html)。

## [未发布]

### 新增
- Taurus Auth 初始发布
- 基于 Macaroon 令牌的票据认证
- 后端服务的 JWT 认证
- IP 白名单安全层
- 请求限流保护
- 所有票据操作的审计日志
- Redis 缓存支持票据验证
- Django REST Framework API
- 完整的测试套件
- Docker 支持

### 更改
- 从 Orion Auth 重命名为 Taurus Auth

## [0.1.0] - 2024-01-01

### 新增
- 初始项目结构
- 基本的票据生成和验证
- JWT 令牌认证
- 数据库模型和迁移
