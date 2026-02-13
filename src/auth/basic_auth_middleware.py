import base64
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from typing import List


class BasicAuthMiddleware(BaseHTTPMiddleware):
    """
    Optional HTTP Basic Authentication middleware.

    If password is None, authentication is disabled and all requests pass through.
    If password is set, all non-OPTIONS requests must provide valid Basic Auth credentials.

    Username is always "user" (hardcoded).
    Password, realm, and allowed_origins are configurable.
    """

    def __init__(self, app, password: str = None, realm: str = "API", allowed_origins: List[str] = None):
        super().__init__(app)
        self.password = password
        self.realm = realm
        self.username = "user"
        self.allowed_origins = allowed_origins or []

    async def dispatch(self, request, call_next):
        # If no password configured, skip authentication entirely
        if self.password is None:
            return await call_next(request)

        # Skip authentication for OPTIONS requests (CORS preflight)
        if request.method == "OPTIONS":
            return await call_next(request)

        # Get Authorization header
        auth_header = request.headers.get("Authorization")

        if not auth_header or not auth_header.startswith("Basic "):
            return self._unauthorized_response(request)

        # Decode and validate credentials
        try:
            encoded_credentials = auth_header[6:]  # Remove "Basic " prefix
            decoded_bytes = base64.b64decode(encoded_credentials)
            credentials = decoded_bytes.decode("utf-8")
            username, password = credentials.split(":", 1)

            if username == self.username and password == self.password:
                return await call_next(request)
        except Exception:
            pass

        # Authentication failed
        return self._unauthorized_response(request)

    def _unauthorized_response(self, request):
        """
        Return 401 response with CORS headers.

        CORS headers are necessary on 401 responses so that browser JavaScript
        can read the WWW-Authenticate header for the authentication challenge.
        """
        headers = {"WWW-Authenticate": f'Basic realm="{self.realm}"'}

        # Add CORS headers if the request origin is allowed
        origin = request.headers.get("origin")
        if origin and self._is_origin_allowed(origin):
            headers["Access-Control-Allow-Origin"] = origin
            headers["Access-Control-Allow-Credentials"] = "true"
            headers["Access-Control-Expose-Headers"] = "WWW-Authenticate"

        return Response(
            status_code=401,
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
