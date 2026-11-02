from reelshelf.security.passwords import Argon2PasswordHasher


async def test_hash_can_be_verified() -> None:
    hasher = Argon2PasswordHasher()
    password = "StrongPassword123!"

    password_hash = await hasher.hash(password)

    assert password_hash != password
    assert password_hash.startswith("$argon2")
    assert await hasher.verify(password, password_hash) is True
    assert await hasher.verify("WrongPassword123!", password_hash) is False


async def test_same_password_produces_different_hashes() -> None:
    hasher = Argon2PasswordHasher()
    password = "StrongPassword123!"

    first = await hasher.hash(password)
    second = await hasher.hash(password)

    assert first != second
    assert await hasher.verify(password, first) is True
    assert await hasher.verify(password, second) is True
