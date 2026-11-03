from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt
import pytest

from reelshelf.domain.errors import UnauthorizedError
from reelshelf.security.tokens import JWTAccessTokenCodec

SECRET = "test-secret-" + "x" * 48
ISSUER = "reelshelf"
AUDIENCE = "reelshelf-api"


@pytest.fixture
def codec() -> JWTAccessTokenCodec:
    return JWTAccessTokenCodec(
        secret=SECRET,
        access_token_minutes=15,
        issuer=ISSUER,
        audience=AUDIENCE,
    )


def make_payload() -> dict[str, object]:
    now = datetime.now(UTC)

    return {
        "sub": str(uuid4()),
        "jti": str(uuid4()),
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=15)).timestamp()),
        "iss": ISSUER,
        "aud": AUDIENCE,
        "token_type": "access",
    }


def test_created_token_returns_its_user_id(
    codec: JWTAccessTokenCodec,
) -> None:
    user_id = uuid4()

    token = codec.create(user_id)

    assert codec.decode(token) == user_id


def test_token_has_expected_claims(
    codec: JWTAccessTokenCodec,
) -> None:
    user_id = uuid4()
    token = codec.create(user_id)

    payload = jwt.decode(
        token,
        SECRET,
        algorithms=["HS256"],
        issuer=ISSUER,
        audience=AUDIENCE,
    )

    assert payload["sub"] == str(user_id)
    assert payload["token_type"] == "access"
    assert payload["exp"] - payload["iat"] == 15 * 60
    assert payload["jti"]


def test_expired_token_is_rejected(
    codec: JWTAccessTokenCodec,
) -> None:
    payload = make_payload()
    now = datetime.now(UTC)

    payload["iat"] = int((now - timedelta(hours=1)).timestamp())
    payload["exp"] = int((now - timedelta(minutes=1)).timestamp())

    token = jwt.encode(payload, SECRET, algorithm="HS256")

    with pytest.raises(UnauthorizedError):
        codec.decode(token)


def test_wrong_signature_is_rejected(
    codec: JWTAccessTokenCodec,
) -> None:
    token = jwt.encode(
        make_payload(),
        "different-secret-" + "y" * 48,
        algorithm="HS256",
    )

    with pytest.raises(UnauthorizedError):
        codec.decode(token)


@pytest.mark.parametrize(
    ("claim", "value"),
    [
        ("iss", "another-issuer"),
        ("aud", "another-api"),
        ("token_type", "refresh"),
        ("sub", "not-a-uuid"),
        ("jti", "not-a-uuid"),
        ("iat", True),
    ],
)
def test_invalid_claims_are_rejected(
    codec: JWTAccessTokenCodec,
    claim: str,
    value: object,
) -> None:
    payload = make_payload()
    payload[claim] = value

    token = jwt.encode(payload, SECRET, algorithm="HS256")

    with pytest.raises(UnauthorizedError):
        codec.decode(token)


@pytest.mark.parametrize(
    "claim",
    ["sub", "jti", "iat", "exp", "iss", "aud", "token_type"],
)
def test_missing_claim_is_rejected(
    codec: JWTAccessTokenCodec,
    claim: str,
) -> None:
    payload = make_payload()
    del payload[claim]

    token = jwt.encode(payload, SECRET, algorithm="HS256")

    with pytest.raises(UnauthorizedError):
        codec.decode(token)


def test_unexpected_algorithm_is_rejected(
    codec: JWTAccessTokenCodec,
) -> None:
    token = jwt.encode(make_payload(), SECRET, algorithm="HS384")

    with pytest.raises(UnauthorizedError):
        codec.decode(token)


def test_malformed_token_is_rejected(
    codec: JWTAccessTokenCodec,
) -> None:
    with pytest.raises(UnauthorizedError):
        codec.decode("not-a-jwt")
