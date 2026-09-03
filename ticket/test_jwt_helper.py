"""
ticket/utils/jwt_helper.py unit tests

Test contents:
1. BackendJWTGenerator.generate_token - Generate JWT Token
2. BackendJWTGenerator.verify_token - Verify JWT Token
"""
import jwt
import pytest
from datetime import datetime, timedelta

from ticket.utils.jwt_helper import BackendJWTGenerator


class TestBackendJWTGeneratorGenerateToken:
    def test_returns_string(self):
        gen = BackendJWTGenerator(secret="test-secret")
        token = gen.generate_token()
        assert isinstance(token, str)

    def test_contains_required_claims(self):
        gen = BackendJWTGenerator(secret="test-secret")
        token = gen.generate_token()
        payload = jwt.decode(token, "test-secret", algorithms=["HS256"])
        assert "sub" in payload
        assert "iat" in payload
        assert "exp" in payload
        assert "nbf" in payload

    def test_default_service_id(self):
        gen = BackendJWTGenerator(secret="test-secret")
        token = gen.generate_token()
        payload = jwt.decode(token, "test-secret", algorithms=["HS256"])
        assert payload["sub"] == "taurus-backend"

    def test_custom_service_id(self):
        gen = BackendJWTGenerator(secret="test-secret")
        token = gen.generate_token(service_id="custom-service")
        payload = jwt.decode(token, "test-secret", algorithms=["HS256"])
        assert payload["sub"] == "custom-service"

    def test_with_ip(self):
        gen = BackendJWTGenerator(secret="test-secret")
        token = gen.generate_token(ip="192.168.1.1")
        payload = jwt.decode(token, "test-secret", algorithms=["HS256"])
        assert payload["ip"] == "192.168.1.1"

    def test_without_ip(self):
        gen = BackendJWTGenerator(secret="test-secret")
        token = gen.generate_token()
        payload = jwt.decode(token, "test-secret", algorithms=["HS256"])
        assert "ip" not in payload

    def test_with_extra_claims(self):
        gen = BackendJWTGenerator(secret="test-secret")
        token = gen.generate_token(extra_claims={"role": "admin"})
        payload = jwt.decode(token, "test-secret", algorithms=["HS256"])
        assert payload["role"] == "admin"

    def test_custom_expires_minutes(self):
        gen = BackendJWTGenerator(secret="test-secret", expires_minutes=5)
        token = gen.generate_token()
        payload = jwt.decode(token, "test-secret", algorithms=["HS256"])
        assert payload["exp"] - payload["iat"] == 300


class TestBackendJWTGeneratorVerifyToken:
    def test_valid_token(self):
        gen = BackendJWTGenerator(secret="test-secret")
        token = gen.generate_token()
        result = gen.verify_token(token)
        assert result["valid"] is True
        assert "payload" in result
        assert result["payload"]["sub"] == "taurus-backend"

    def test_expired_token(self):
        gen = BackendJWTGenerator(secret="test-secret")
        now = datetime.utcnow()
        payload = {
            "sub": "taurus-backend",
            "iat": now - timedelta(hours=2),
            "exp": now - timedelta(hours=1),
            "nbf": now - timedelta(hours=2),
        }
        token = jwt.encode(payload, "test-secret", algorithm="HS256")
        result = gen.verify_token(token)
        assert result["valid"] is False
        assert "Token has expired" in result["reason"]

    def test_wrong_secret(self):
        gen1 = BackendJWTGenerator(secret="correct-secret")
        gen2 = BackendJWTGenerator(secret="wrong-secret")
        token = gen1.generate_token()
        result = gen2.verify_token(token)
        assert result["valid"] is False
        assert "Invalid Token" in result["reason"]

    def test_invalid_token_format(self):
        gen = BackendJWTGenerator(secret="test-secret")
        result = gen.verify_token("not-a-valid-token")
        assert result["valid"] is False

    def test_missing_required_claims(self):
        gen = BackendJWTGenerator(secret="test-secret")
        payload = {"sub": "test"}
        token = jwt.encode(payload, "test-secret", algorithm="HS256")
        result = gen.verify_token(token)
        assert result["valid"] is False