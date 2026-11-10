.PHONY: setup run format check test init-env dev

setup:
	uv sync --locked

run:
	uv run --locked uvicorn reelshelf.main:create_app --factory --reload

format:
	uv run --locked ruff check --fix .
	uv run --locked ruff format .

check:
	uv run --locked ruff check .
	uv run --locked ruff format --check .
	uv run --locked mypy src tests scripts
	uv run --locked pytest --cov=reelshelf --cov-report=term-missing --cov-fail-under=80

test:
	uv run --locked pytest --cov=reelshelf --cov-report=term-missing --cov-fail-under=80

init-env:
	uv run --locked python scripts/init_env.py

dev:
	$(MAKE) setup
	$(MAKE) init-env
	$(MAKE) run