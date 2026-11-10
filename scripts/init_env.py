from pathlib import Path
from secrets import token_urlsafe


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    target = root / ".env"

    if target.exists():
        print("Keeping existing .env")
        return

    template = (root / ".env.example").read_text(encoding="utf-8")
    marker = "REELSHELF_JWT_SECRET="

    if template.splitlines().count(marker) != 1:
        raise ValueError("Expected exactly one empty JWT secret in .env.example")

    content = template.replace(marker, marker + token_urlsafe(48), 1)

    with target.open("x", encoding="utf-8") as stream:
        stream.write(content)

    target.chmod(0o600)
    print("Created .env with a generated local secret")


if __name__ == "__main__":
    main()
