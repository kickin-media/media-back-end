import base64
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from typing import List


class SitewidePasswordMiddleware(BaseHTTPMiddleware):
    """
    Optional sitewide password authentication middleware using a custom header.

    If password is None, authentication is disabled and all requests pass through.
    If password is set, all non-OPTIONS requests must provide a valid password
    in the X-Sitewide-Password header (base64-encoded).

    This uses a custom header (X-Sitewide-Password) instead of HTTP Basic Auth
    to avoid conflicts with Bearer token authentication on the Authorization header.
    """

    def __init__(self, app, password: str = None, hint: str = None, allowed_origins: List[str] = None):
        super().__init__(app)
        self.password = password
        self.hint = hint or "Password required"
        self.allowed_origins = allowed_origins or []

    async def dispatch(self, request, call_next):
        # If no password configured, skip authentication entirely
        if self.password is None:
            return await call_next(request)

        # Skip authentication for OPTIONS requests (CORS preflight)
        if request.method == "OPTIONS":
            return await call_next(request)

        # Get X-Sitewide-Password header
        password_header = request.headers.get("X-Sitewide-Password")

        if not password_header:
            return self._unauthorized_response(request)

        # Decode and validate password
        try:
            decoded_bytes = base64.b64decode(password_header)
            provided_password = decoded_bytes.decode("utf-8")

            if provided_password == self.password:
                return await call_next(request)
        except Exception:
            pass

        # Authentication failed
        return self._unauthorized_response(request)

    def _unauthorized_response(self, request):
        """
        Return 401 response with hint and CORS headers.

        CORS headers are necessary on 401 responses so that browser JavaScript
        can process the authentication challenge.
        """
        headers = {}

        # Add CORS headers if the request origin is allowed
        origin = request.headers.get("origin")
        if origin and self._is_origin_allowed(origin):
            headers["Access-Control-Allow-Origin"] = origin
            headers["Access-Control-Allow-Credentials"] = "true"
            headers["Access-Control-Expose-Headers"] = "*"

        return JSONResponse(
            status_code=401,
            content={
                "error": "authentication_required",
                "hint": self.hint
            },
            headers=headers
        )

    def _is_origin_allowed(self, origin: str) -> bool:
        """Check if the origin is in the allowed origins list."""
        if not self.allowed_origins:
            return False

        # Check for wildcard
        if "*" in self.allowed_origins:
            return True

        # Check if origin matches any allowed origin
        return origin in self.allowed_origins
