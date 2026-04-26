run:
	docker compose -f hosting/compose.yml --env-file api/.env up --build -d

stop:
	docker compose -f hosting/compose.yml --env-file api/.env down

test_ci_workflow:
	@command -v act > /dev/null 2>&1 || (echo "Error: 'act' is not installed or not in PATH. See https://github.com/nektos/act" && exit 1)
	@if [ -z "$(GH_TOKEN)" ]; then \
		echo "Error: Please provide a github token. Usage: make test_ci_workflow GH_TOKEN=<your-github-pat>"; \
		exit 1; \
	fi
	@echo "Running CI workflow..."
	act workflow_dispatch --input version=0.2.0 --secret GH_TOKEN=$(GH_TOKEN) --secret TEST_PYPI_TOKEN=$(TEST_PYPI_TOKEN) --artifact-server-path /tmp/act-artifacts

add_migration:
	chmod 777 api/migrations/versions/
	@if [ -z "$(MSG)" ]; then \
		echo "Error: Please provide a message. Usage: make add_migration MSG='your migration message'"; \
		exit 1; \
	fi
	docker compose -f hosting/compose.yml --env-file api/.env exec api python -m alembic revision --autogenerate -m "$(MSG)"
	chmod 777 api/migrations/versions/

run_migrations:
	docker compose -f hosting/compose.yml --env-file api/.env exec api python -m alembic upgrade head

revert_migrations:
	docker compose -f hosting/compose.yml --env-file api/.env exec api python -m alembic downgrade -1
