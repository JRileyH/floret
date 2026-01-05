"""Request logging middleware for monitoring traffic patterns."""

import logging

logger = logging.getLogger("floret.requests")


class RequestLoggingMiddleware:
    """
    Logs request details including IP and user agent for monitoring traffic patterns.

    This is useful for identifying bots, suspicious traffic, or analyzing usage patterns.
    Logs are sent to Loki where you can query by IP, user agent, or endpoint.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Get client IP (handles proxy headers like X-Forwarded-For)
        ip = self.get_client_ip(request)
        user_agent = request.META.get("HTTP_USER_AGENT", "unknown")
        method = request.method
        path = request.path

        # Process the request
        response = self.get_response(request)

        # Log completed requests with status code
        logger.info(
            f"{method} {path}",
            extra={
                "ip": ip,
                "user_agent": user_agent,
                "method": method,
                "path": path,
                "status_code": response.status_code,
                "user_id": request.user.id if request.user.is_authenticated else None,
                "email": request.user.email if request.user.is_authenticated else None,
            },
        )

        return response

    def get_client_ip(self, request):
        """Extract client IP, handling proxy headers."""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            # X-Forwarded-For can contain multiple IPs, first one is the client
            ip = x_forwarded_for.split(",")[0].strip()
        else:
            ip = request.META.get("REMOTE_ADDR")
        return ip
