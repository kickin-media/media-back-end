from fastapi import Request, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from variables import JWT_KEY_CERTIFICATE, JWT_AUDIENCE

import time
import jwt


def decode_jwt(token: str) -> dict:
    try:
        decoded_token = jwt.decode(token, key=JWT_KEY_CERTIFICATE, audience=JWT_AUDIENCE, algorithms=["RS256"])
        return decoded_token if decoded_token["exp"] >= time.time() else None
    except Exception:
        return {}


class JWTBearer(HTTPBearer):
    _required_permissions = None
    _auto_error = None

    def __init__(self, auto_error: bool = True, required_permissions: list = None):
        self._required_permissions = required_permissions
        self.auto_error = auto_error
        super(JWTBearer, self).__init__(auto_error=auto_error)

    async def __call__(self, request: Request):
        credentials: HTTPAuthorizationCredentials = await super(JWTBearer, self).__call__(request)
        if credentials:
            if not credentials.scheme == "Bearer":
                raise HTTPException(status_code=403, detail="invalid_auth_scheme")
            if not self.verify_jwt(credentials.credentials):
                raise HTTPException(status_code=403, detail="token_invalid_or_expired")

            decoded_jwt = decode_jwt(credentials.credentials)

            # Verify required scopes.
            if self._required_permissions is not None:
                for permission in self._required_permissions:
                    if permission not in decoded_jwt['permissions']:
                        raise HTTPException(status_code=403, detail="missing_permission_{}".format(permission))

            return decoded_jwt
        else:
            if self._auto_error:
                raise HTTPException(status_code=403, detail="invalid_auth_code")
            else:
                return None

    def verify_jwt(self, jwtoken: str) -> bool:
        isTokenValid: bool = False

        try:
            payload = decode_jwt(jwtoken)
        except Exception:
            payload = None
        if payload:
            isTokenValid = True
        return isTokenValid
