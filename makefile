run:
	docker compose -f hosting/compose.yml --env-file api/.env up --build -d

stop:
	docker compose -f hosting/compose.yml --env-file api/.env down

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
