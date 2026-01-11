check:
	ruff format
	ruff check --fix
	pyright
	mypy .

api:
	./.venv/bin/python -m services.api

