venv := if os_family() == "windows" { "./.venv/Scripts" } else { "./.venv/bin" }

check: format type-check test
    
# runs basedpyright
type-check:
    {{venv}}/basedpyright


lint:
    {{venv}}/ruff check


# formats code with ruff
format:
    {{venv}}/ruff format
    {{venv}}/ruff check --fix


test:
    {{venv}}/pytest

test-cov:
    {{venv}}/pytest --cov=services --cov-report=term-missing

# options: api, auth, game
run APP:
    {{venv}}/python -m services.{{APP}}


ui *ARGS:
    cd ./services/ui/; pnpm {{ARGS}}

# starts all services with infra in docker
up:
    docker compose -f services-compose.yml up -d

# stops all services with infra in docker
down:
    docker compose -f services-compose.yml down

generate-proto:
	cp ./proto/*.proto ./generated/
	{{venv}}/python \
		-m grpc_tools.protoc \
		-I . \
		--python_out=. \
		--grpc_python_out=. \
		--mypy_out=. \
		--mypy_grpc_out=. \
		./generated/*.proto
	rm ./generated/*.proto


# options: auth, game
make-migrations APP:
    {{venv}}/alembic -c ./services/{{APP}}/alembic.ini revision --autogenerate

# options: auth, game
apply-migrations APP:
    {{venv}}/alembic -c ./services/{{APP}}/alembic.ini upgrade head

# options: auth, game
rollback APP:
    {{venv}}/alembic -c ./services/{{APP}}/alembic.ini downgrade base


# options: auth, game
connect-to-db APP:
	docker exec -it {{APP}}-postgres psql -U duo_{{APP}} -d duo_{{APP}}


# linux/mac only: on windows use 'for /d /r . %d in (__pycache__) do @rd /s /q "%d" & del /s /q *.pyc'
clean:
    find . -type d -name __pycache__ -exec rm -rf {} +
    find . -name "*.pyc" -delete
