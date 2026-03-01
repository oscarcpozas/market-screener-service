serve:
	uv run fastapi dev src/app.py

worker:
	uv run celery -A src.core.worker worker --loglevel=info

beat:
	uv run celery -A src.core.worker beat --loglevel=info

lint:
	uv run --group lint ruff check src/

test:
	APP_ENV=test uv run --group test pytest tests/ -v

flayway-migrate:
	docker compose run --rm flyway migrate

flayway-migrate-info:
	docker compose run --rm flyway info
