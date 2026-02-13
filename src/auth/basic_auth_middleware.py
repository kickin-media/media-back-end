import base64
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


class BasicAuthMiddleware(BaseHTTPMiddleware):
    """
    Optional HTTP Basic Authentication middleware.

    If password is None, authentication is disabled and all requests pass through.
    If password is set, all non-OPTIONS requests must provide valid Basic Auth credentials.

    Username is always "user" (hardcoded).
    Password and realm are configurable.
    """

    def __init__(self, app, password: str = None, realm: str = "API"):
        super().__init__(app)
        self.password = password
        self.realm = realm
        self.username = "user"

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
            return self._unauthorized_response()

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
        return self._unauthorized_response()

    def _unauthorized_response(self):
        return Response(
            status_code=401,
            headers={"WWW-Authenticate": f'Basic realm="{self.realm}"'}
        )
