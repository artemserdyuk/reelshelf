from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import jwt
from jwt.exceptions import InvalidTokenError

from reelshelf.domain.errors import UnauthorizedError

JWT_ALGORITHM = "HS256"
TOKEN_TYPE_ACCESS = "access"


class JWTAccessTokenCodec:
    def __init__(
        self,
        *,
        secret: str,
        access_token_minutes: int,
        issuer: str,
        audience: str,
    ) -> None:
        self._secret = secret
        self._lifetime = timedelta(minutes=access_token_minutes)
        self._issuer = issuer
        self._audience = audience

    def create(self, user_id: UUID) -> str:
        now = datetime.now(UTC)

        payload = {
            "sub": str(user_id),
            "jti": str(uuid4()),
            "iat": int(now.timestamp()),
            "exp": int((now + self._lifetime).timestamp()),
            "iss": self._issuer,
            "aud": self._audience,
            "token_type": TOKEN_TYPE_ACCESS,
        }

        return jwt.encode(
            payload,
            self._secret,
            algorithm=JWT_ALGORITHM,
        )

    def decode(self, token: str) -> UUID:
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
            if payload["token_type"] != TOKEN_TYPE_ACCESS:
                raise ValueError("Unexpected token type.")

            subject = payload["sub"]
            token_id = payload["jti"]
            issued_at = payload["iat"]
            expires_at = payload["exp"]

            if not isinstance(subject, str) or not isinstance(token_id, str):
                raise ValueError("Invalid identifier claims.")

            # Require integer timestamps; bool is not accepted.
            if type(issued_at) is not int or type(expires_at) is not int:
                raise ValueError("Invalid timestamp claims.")

            if expires_at <= issued_at:
                raise ValueError("Invalid token lifetime.")

            # Validate both identifiers, although only the user ID is returned.
            UUID(token_id)
            return UUID(subject)

        except (InvalidTokenError, ValueError, TypeError) as exc:
            raise UnauthorizedError("Invalid or expired access token.") from exc
