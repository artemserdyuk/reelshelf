from datetime import UTC, datetime
from uuid import UUID

import jwt
from jwt.exceptions import InvalidTokenError

from reelshelf.domain.errors import UnauthorizedError
from reelshelf.domain.tokens import RefreshClaims

JWT_ALGORITHM = "HS256"
TOKEN_REFRESH_TYPE = "refresh"


class JWTRefreshTokenCodec:
    def __init__(self, *, secret: str, issuer: str, audience: str) -> None:
        self._secret = secret
        self._issuer = issuer
        self._audience = audience

    def create(self, claims: RefreshClaims) -> str:
        payload = {
            "sub": str(claims.user_id),
            "jti": str(claims.jti),
            "iat": int(datetime.now(UTC).timestamp()),
            "exp": int(claims.expires_at.timestamp()),
            "iss": self._issuer,
            "aud": self._audience,
            "token_type": "refresh",
        }
        return jwt.encode(payload, self._secret, algorithm="HS256")

    def decode(self, token: str) -> RefreshClaims:
        try:
            payload = jwt.decode(
                token,
                self._secret,
                algorithms=[JWT_ALGORITHM],
                issuer=self._issuer,
                audience=self._audience,
                options={
                    "require": [
                        "sub",
                        "jti",
                        "iat",
                        "exp",
                        "iss",
                        "aud",
                        "token_type",
                    ],
                },
            )

            # These are application-specific claim checks.
            if payload["token_type"] != TOKEN_REFRESH_TYPE:
                raise ValueError("Unexpected token type.")

            subject = payload["sub"]
            token_id = payload["jti"]
            issued_at = payload["iat"]
            expires_at = payload["exp"]

            if not isinstance(subject, str) or not isinstance(token_id, str):
                raise ValueError("Invalid identifiers.")

            if type(issued_at) is not int or type(expires_at) is not int:
                raise ValueError("Invalid timestamps.")

            if expires_at <= issued_at:
                raise ValueError("Invalid lifetime.")

            return RefreshClaims(
                user_id=UUID(subject),
                jti=UUID(token_id),
                expires_at=datetime.fromtimestamp(expires_at, UTC),
            )
        except (
            InvalidTokenError,
            ValueError,
            TypeError,
            OverflowError,
            OSError,
        ) as exc:
            raise UnauthorizedError("Invalid or expired refresh token.") from exc
