.PHONY: setup run format check test

setup:
	uv sync --locked

run:
	uv run --locked uvicorn reelshelf.main:create_app --factory --reload

format:
	uv run ruff check --fix .
	uv run ruff format .

check:
	uv run --locked ruff check .
	uv run --locked ruff format --check .
	uv run --locked mypy src tests
	uv run --locked pytest --cov=reelshelf --cov-report=term-missing --cov-fail-under=80

test:
	uv run --locked pytest --cov=reelshelf --cov-report=term-missing --cov-fail-under=80