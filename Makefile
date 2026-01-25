# PYTHONPATH_SERVICES=services/api:services/users:services/billing
PYTHONPATH_SERVICES=services

type-check:
	.venv/bin/basedpyright
	.venv/bin/mypy .


format:
	.venv/bin/ruff format
	.venv/bin/ruff check --fix


api:
	PYTHONPATH=$(PYTHONPATH_SERVICES) ./.venv/bin/python -m services.api


ui:
	cd ./services/ui/; npm run dev

