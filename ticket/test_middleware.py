"""
ticket/middleware.py SecurityMiddleware unit tests

Test contents:
1. Health check path passthrough
2. IP whitelist check
3. Request rate limiting
4. Security header addition
5. Client IP retrieval
"""
from unittest.mock import patch, MagicMock

from django.test import TestCase, RequestFactory, override_settings

from ticket.middleware import SecurityMiddleware


class SecurityMiddlewareHealthCheckTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = SecurityMiddleware(lambda request: None)

    def test_health_path_passes(self):
        request = self.factory.get("/health/")
        result = self.middleware.process_request(request)
        assert result is None

    def test_static_path_passes(self):
        request = self.factory.get("/static/style.css")
        result = self.middleware.process_request(request)
        assert result is None

    @patch("ticket.middleware.cache")
    def test_api_path_is_checked(self, mock_cache):
        mock_cache.get.return_value = 0
        mock_cache.set.return_value = None
        request = self.factory.get("/api/v1/tickets/generate")
        result = self.middleware.process_request(request)
        assert result is None


class SecurityMiddlewareIPWhitelistTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = SecurityMiddleware(lambda request: None)

    @override_settings(ALLOWED_BACKEND_IPS=[])
    def test_empty_whitelist_passes(self):
        request = self.factory.get("/api/v1/tickets/generate")
        result = self.middleware._check_ip_whitelist(request)
        assert result is None

    @override_settings(ALLOWED_BACKEND_IPS=["10.0.0.1"])
    def test_allowed_ip_passes(self):
        request = self.factory.get(
            "/api/v1/tickets/generate",
            REMOTE_ADDR="10.0.0.1",
        )
        result = self.middleware._check_ip_whitelist(request)
        assert result is None

    @override_settings(ALLOWED_BACKEND_IPS=["10.0.0.1"])
    def test_blocked_ip_rejected(self):
        request = self.factory.get(
            "/api/v1/tickets/generate",
            REMOTE_ADDR="192.168.1.1",
        )
        result = self.middleware._check_ip_whitelist(request)
        assert result is not None
        assert result.status_code == 403

    def test_x_forwarded_for_ip(self):
        request = self.factory.get(
            "/api/v1/tickets/generate",
            REMOTE_ADDR="127.0.0.1",
            HTTP_X_FORWARDED_FOR="10.0.0.1, 172.16.0.1",
        )
        ip = self.middleware._get_client_ip(request)
        assert ip == "10.0.0.1"

    def test_remote_addr_fallback(self):
        request = self.factory.get(
            "/api/v1/tickets/generate",
            REMOTE_ADDR="192.168.1.1",
        )
        ip = self.middleware._get_client_ip(request)
        assert ip == "192.168.1.1"


class SecurityMiddlewareRateLimitTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = SecurityMiddleware(lambda request: None)
        self._cache_store = {}

    def _mock_cache_get(self, key, default=None):
        return self._cache_store.get(key, default)

    def _mock_cache_set(self, key, value, timeout=None):
        self._cache_store[key] = value

    @override_settings(RATELIMIT_ENABLE=False)
    def test_disabled_ratelimit_passes(self):
        request = self.factory.get("/api/v1/tickets/generate", REMOTE_ADDR="10.0.0.1")
        result = self.middleware._check_rate_limit(request)
        assert result is None

    @override_settings(RATELIMIT_ENABLE=True, RATELIMIT_RATE="3/m")
    @patch("ticket.middleware.cache")
    def test_within_limit_passes(self, mock_cache):
        call_count = [0]

        def mock_get(key, default=None):
            return self._cache_store.get(key, default)

        def mock_set(key, value, timeout=None):
            self._cache_store[key] = value

        mock_cache.get.side_effect = mock_get
        mock_cache.set.side_effect = mock_set

        for _ in range(3):
            request = self.factory.get("/api/v1/tickets/generate", REMOTE_ADDR="10.0.0.1")
            result = self.middleware._check_rate_limit(request)
            assert result is None

    @override_settings(RATELIMIT_ENABLE=True, RATELIMIT_RATE="3/m")
    @patch("ticket.middleware.cache")
    def test_exceeds_limit_blocked(self, mock_cache):
        self._cache_store = {}

        def mock_get(key, default=None):
            return self._cache_store.get(key, default)

        def mock_set(key, value, timeout=None):
            self._cache_store[key] = value

        mock_cache.get.side_effect = mock_get
        mock_cache.set.side_effect = mock_set

        for _ in range(3):
            request = self.factory.get("/api/v1/tickets/generate", REMOTE_ADDR="10.0.0.1")
            self.middleware._check_rate_limit(request)

        request = self.factory.get("/api/v1/tickets/generate", REMOTE_ADDR="10.0.0.1")
        result = self.middleware._check_rate_limit(request)
        assert result is not None
        assert result.status_code == 429

    @override_settings(RATELIMIT_ENABLE=True, RATELIMIT_RATE="3/m")
    @patch("ticket.middleware.cache")
    def test_different_ips_independent(self, mock_cache):
        self._cache_store = {}

        def mock_get(key, default=None):
            return self._cache_store.get(key, default)

        def mock_set(key, value, timeout=None):
            self._cache_store[key] = value

        mock_cache.get.side_effect = mock_get
        mock_cache.set.side_effect = mock_set

        for _ in range(3):
            request = self.factory.get("/api/v1/tickets/generate", REMOTE_ADDR="10.0.0.1")
            self.middleware._check_rate_limit(request)

        request = self.factory.get("/api/v1/tickets/generate", REMOTE_ADDR="10.0.0.2")
        result = self.middleware._check_rate_limit(request)
        assert result is None


class SecurityMiddlewareSecurityHeadersTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = SecurityMiddleware(lambda request: None)

    def test_adds_request_start_header(self):
        request = self.factory.get("/api/v1/tickets/generate")
        self.middleware._add_security_headers(request)
        assert "X-Request-Start" in request.META