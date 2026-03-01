# Crypto Market Screener

A FastAPI-based cryptocurrency market screening application.

## Requirements

- Python 3.12.12
- [uv](https://docs.astral.sh/uv) package manager

## Set up

This project uses [uv](https://docs.astral.sh/uv) as a package/project manager. uv will automatically resolve and lock the project dependencies (i.e., create a uv.lock alongside the pyproject.toml), create a virtual environment, and run commands in that environment.

## Development

### Run the development server

```bash
make serve
```

This starts the FastAPI development server with hot-reload enabled.

### Linting

```bash
make lint
```

uv run will automatically resolve and lock the project dependencies (i.e., create a uv.lock alongside the pyproject.toml), create a virtual environment, and run the command in that environment.


Check the API docs at http://localhost:8000/docs#/