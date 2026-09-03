"""
JWT utility class: used by taurus-backend to generate JWT Tokens
"""
import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict


class BackendJWTGenerator:
    """Backend JWT Generator"""

    def __init__(
        self,
        secret: str,
        algorithm: str = "HS256",
        expires_minutes: int = 60,
    ):
        self.secret = secret
        self.algorithm = algorithm
        self.expires_minutes = expires_minutes

    def generate_token(
        self,
        service_id: str = "taurus-backend",
        ip: Optional[str] = None,
        extra_claims: Optional[Dict] = None,
    ) -> str:
        now = datetime.utcnow()

        payload = {
            "sub": service_id,
            "iat": now,
            "exp": now + timedelta(minutes=self.expires_minutes),
            "nbf": now,
        }

        if ip:
            payload["ip"] = ip

        if extra_claims:
            payload.update(extra_claims)

        token = jwt.encode(payload, self.secret, algorithm=self.algorithm)

        return token

    def verify_token(self, token: str) -> Dict:
        try:
            payload = jwt.decode(
                token,
                self.secret,
                algorithms=[self.algorithm],
                options={
                    "require": ["exp", "iat", "sub"],
                    "verify_exp": True,
                },
            )
            return {"valid": True, "payload": payload}
        except jwt.ExpiredSignatureError:
            return {"valid": False, "reason": "Token has expired"}
        except jwt.InvalidTokenError as e:
            return {"valid": False, "reason": f"Invalid Token: {str(e)}"}