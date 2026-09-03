# 安全策略

## 报告漏洞

Taurus Auth 项目非常重视安全。如果您发现了安全漏洞，请负责任地披露。

**请不要在公共问题追踪器中报告安全漏洞。**

相反，请通过以下方式报告：

- **电子邮件**：taurus-stack@outlook.com
- **主题**：`[Taurus Auth Security] <漏洞简要描述>`

请包含以下信息：

1. **漏洞描述**：漏洞是什么以及它如何影响系统
2. **复现步骤**：如何复现该问题的逐步说明
3. **影响范围**：受影响的版本和组件
4. **严重程度**：您对严重程度的评估（低/中/高/严重）
5. **建议修复**（如适用）

## 披露政策

我们遵循协调披露流程：

1. **报告**：您向我们发送漏洞详情
2. **确认**：我们在 48 小时内确认收到您的报告
3. **调查**：我们调查并验证漏洞
4. **修复**：我们开发并测试补丁
5. **发布**：我们发布安全更新并公开披露

## 支持的版本

只有最新的稳定版本会收到安全更新。

| 版本 | 支持状态 |
|------|----------|
| 最新稳定版 | ✅ 完全支持 |
| 前一个主要版本 | ⚠️ 仅限关键安全修复 |
| 更早版本 | ❌ 不支持 |

## 安全架构

### 认证
- JWT Token 认证（HMAC-SHA256 签名）
- 可配置的 Token 过期时间
- 服务标识验证

### 授权
- IP 白名单限制
- 允许的服务标识列表
- 票据操作权限控制

### 数据保护
- 传输中加密：HTTPS
- Macaroon 票据加密
- Nonce 防重放攻击
- 审计日志追踪

## 安全最佳实践

部署 Taurus Auth 时，请遵循以下实践：

1. **使用强 JWT 密钥**：生成密码学强度的密钥
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

2. **限制 IP 白名单**：仅允许受信任的后端服务 IP
   ```bash
   ALLOWED_BACKEND_IPS=10.0.0.0/24,172.16.0.0/16
   ```

3. **启用请求限流**：防止暴力攻击
   ```bash
   RATELIMIT_ENABLE=True
   RATELIMIT_RATE=100/m
   ```

4. **使用 HTTPS**：生产环境始终使用 HTTPS
   ```nginx
   server {
       listen 443 ssl;
       ssl_certificate /path/to/cert.pem;
       ssl_certificate_key /path/to/key.pem;
   }
   ```

5. **保护 Macaroon 根密钥**：使用强随机密钥
   ```bash
   MACAROON_ROOT_KEY=your-strong-random-key
   ```

6. **限制票据过期时间**：使用适当的过期时间
   ```bash
   TICKET_DEFAULT_EXPIRES_MINUTES=5
   TICKET_MAX_EXPIRES_MINUTES=60
   ```

7. **监控审计日志**：定期审查审计日志以发现可疑活动
   ```bash
   GET /api/v1/tickets/audit-logs?event=verified
   ```

8. **保持依赖更新**：定期更新 Python 包
   ```bash
   poetry update
   ```

## 安全特性

Taurus Auth 包含以下安全特性：

- **JWT 认证**：HMAC-SHA256 签名的 Token，可配置过期时间
- **IP 白名单**：限制特定后端服务 IP 的访问
- **请求限流**：可配置的速率限制防止滥用
- **Macaroon 票据**：一次性使用的票据，支持密码学验证
- **审计日志**：完整的票据操作审计追踪
- **Nonce 验证**：通过 Nonce 追踪防止重放攻击
- **票据过期**：未使用票据的自动过期
- **票据撤销**：在过期前撤销票据的能力

## 已知限制

1. JWT Token 是无状态的，无法在过期前撤销
2. Macaroon 票据需要 Redis 进行 Nonce 追踪
3. 限流是基于 IP 的，可能无法防护分布式攻击
4. IP 白名单在后端 IP 变化时需要手动更新

## 合规性

Taurus Auth 遵循安全最佳实践，旨在帮助您符合：

- **OWASP Top 10**：防护常见的 Web 应用漏洞
- **NIST 网络安全框架**：识别、保护、检测、响应、恢复
- **ISO 27001**：信息安全管理系统的标准
