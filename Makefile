type-check:
	.venv/bin/pyright
	.venv/bin/mypy .


format:
	.venv/bin/ruff format
	.venv/bin/ruff check --fix

api:
	./.venv/bin/python -m services.api

