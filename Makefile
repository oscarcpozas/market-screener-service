serve:
	uv run fastapi dev src/app.py

worker:
	uv run celery -A src.worker worker --loglevel=info

beat:
	uv run celery -A src.worker beat --loglevel=info

lint:
	uv run ruff check src/

test:
	APP_ENV=test uv run --group test pytest tests/ -v

flayway-migrate:
	docker compose run --rm flyway migrate

flayway-migrate-info:
	docker compose run --rm flyway info
