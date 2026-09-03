# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

We take the security of Taurus Auth seriously. If you believe you have found a security vulnerability, please report it to us as described below.

**Please do NOT report security vulnerabilities through public GitHub issues.**

Instead, please report them via email to [taurus-stack@outlook.com](mailto:taurus-stack@outlook.com).

You should receive a response within 48 hours. If for some reason you do not, please follow up via email to ensure we received your original message.

Please include the requested information listed below (as much as you can provide) to help us better understand the nature and scope of the possible issue:

- Type of issue (e.g. buffer overflow, SQL injection, cross-site scripting, etc.)
- Full paths of source file(s) related to the manifestation of the issue
- The location of the affected source code (tag/branch/commit or direct URL)
- Any special configuration required to reproduce the issue
- Step-by-step instructions to reproduce the issue
- Proof-of-concept or exploit code (if possible)
- Impact of the issue, including how an attacker might exploit the issue

This information will help us triage your report more quickly.

## Preferred Languages

We prefer all communications to be in English.

## Security Best Practices

When deploying Taurus Auth in production:

1. **Use strong JWT secrets**: Generate cryptographically strong secrets
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

2. **Restrict IP whitelist**: Only allow trusted backend service IPs
   ```bash
   ALLOWED_BACKEND_IPS=10.0.0.0/24,172.16.0.0/16
   ```

3. **Enable rate limiting**: Protect against brute force attacks
   ```bash
   RATELIMIT_ENABLE=True
   RATELIMIT_RATE=100/m
   ```

4. **Use HTTPS**: Always use HTTPS in production
   ```nginx
   server {
       listen 443 ssl;
       ssl_certificate /path/to/cert.pem;
       ssl_certificate_key /path/to/key.pem;
   }
   ```

5. **Secure Macaroon root key**: Use a strong, unique root key
   ```bash
   MACAROON_ROOT_KEY=your-strong-random-key
   ```

6. **Limit ticket expiration**: Use appropriate expiration times
   ```bash
   TICKET_DEFAULT_EXPIRES_MINUTES=5
   TICKET_MAX_EXPIRES_MINUTES=60
   ```

7. **Monitor audit logs**: Regularly review audit logs for suspicious activity
   ```bash
   GET /api/v1/tickets/audit-logs?event=verified
   ```

8. **Keep dependencies updated**: Regularly update Python packages
   ```bash
   poetry update
   ```

## Security Features

Taurus Auth includes several security features:

- **JWT Authentication**: HMAC-SHA256 signed tokens with configurable expiration
- **IP Whitelist**: Restrict access to specific backend service IPs
- **Rate Limiting**: Protect against abuse with configurable rate limits
- **Macaroon Tickets**: One-time use tickets with cryptographic verification
- **Audit Logging**: Complete audit trail of all ticket operations
- **Nonce Validation**: Prevent replay attacks with nonce tracking
- **Ticket Expiration**: Automatic expiration of unused tickets
- **Ticket Revocation**: Ability to revoke tickets before expiration

## Security Architecture

Taurus Auth implements a three-layer security model:

### Layer 1: IP Whitelist

Restricts access to specific backend service IPs. Requests from non-whitelisted IPs receive 403 Forbidden.

### Layer 2: Rate Limiting

Protects against abuse with configurable rate limits. Exceeding the limit returns 429 Too Many Requests.

### Layer 3: JWT Authentication

All ticket generation and revocation operations require valid JWT tokens signed with the configured secret.

## Known Limitations

1. JWT tokens are stateless and cannot be revoked before expiration
2. Macaroon tickets require Redis for nonce tracking
3. Rate limiting is per-IP and may not protect against distributed attacks
4. IP whitelist requires manual updates when backend IPs change

## Compliance

Taurus Auth follows security best practices and is designed to help you comply with:

- **OWASP Top 10**: Protection against common web application vulnerabilities
- **NIST Cybersecurity Framework**: Identify, Protect, Detect, Respond, Recover
- **ISO 27001**: Information security management system standards
