"""
Security middleware: IP whitelist + request rate limiting + security headers
"""
import logging
import time
from django.conf import settings
from django.http import JsonResponse
from django.core.cache import cache
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


class SecurityMiddleware(MiddlewareMixin):
    """Security middleware"""

    def process_request(self, request):
        path = request.path

        if path.startswith("/health/") or path.startswith("/static/"):
            return None

        if path.startswith("/api/v1/tickets/"):
            ip_result = self._check_ip_whitelist(request)
            if ip_result:
                return ip_result

            rate_result = self._check_rate_limit(request)
            if rate_result:
                return rate_result

            self._add_security_headers(request)

        return None

    def _check_ip_whitelist(self, request):
        allowed_ips = getattr(settings, "ALLOWED_BACKEND_IPS", [])

        if not allowed_ips:
            return None

        client_ip = self._get_client_ip(request)

        if client_ip not in allowed_ips:
            logger.warning(f"IP whitelist rejected: {client_ip} -> {request.path}")
            return JsonResponse(
                {"code": 403, "msg": "IP is not in the whitelist"},
                status=403,
            )

        return None

    def _check_rate_limit(self, request):
        if not getattr(settings, "RATELIMIT_ENABLE", True):
            return None

        client_ip = self._get_client_ip(request)
        rate_str = getattr(settings, "RATELIMIT_RATE", "100/m")

        try:
            rate_count, rate_period = rate_str.split("/")
            rate_count = int(rate_count)

            period_map = {"s": 1, "m": 60, "h": 3600, "d": 86400}
            rate_seconds = period_map.get(rate_period, 60)
        except (ValueError, KeyError):
            rate_count = 100
            rate_seconds = 60

        cache_key = f"ratelimit:{client_ip}:{request.path}"

        current_count = cache.get(cache_key, 0)

        if current_count >= rate_count:
            logger.warning(
                f"Request rate limited: {client_ip} -> {request.path} "
                f"(current: {current_count}, limit: {rate_count}/{rate_seconds}s)"
            )
            return JsonResponse(
                {"code": 429, "msg": "Too many requests, please try again later"},
                status=429,
            )

        cache.set(cache_key, current_count + 1, rate_seconds)

        return None

    def _add_security_headers(self, request):
        request.META["X-Request-Start"] = str(time.time())

    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0].strip()
        else:
            ip = request.META.get("REMOTE_ADDR")
        return ip