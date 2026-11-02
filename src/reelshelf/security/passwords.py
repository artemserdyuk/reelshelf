import asyncio

from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher


class Argon2PasswordHasher:
    def __init__(self) -> None:
        # Explicitly select Argon2 as our password hashing algorithm.
        self._hasher = PasswordHash((Argon2Hasher(),))

    async def hash(self, password: str) -> str:
        # Execute synchronous hashing outside the event-loop thread.
        return await asyncio.to_thread(
            self._hasher.hash,
            password,
        )

    async def verify(
        self,
        password: str,
        password_hash: str,
    ) -> bool:
        # pwdlib expects the password first and the stored hash second.
        return await asyncio.to_thread(
            self._hasher.verify,
            password,
            password_hash,
        )
