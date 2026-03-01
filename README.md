![](resources/banner.webp)

This project aims to provide an example of FastAPI application writter in Python

---

# Development

### Start project dependencies

Check [compose.yml](compose.yml) file

```shell
docker compose up -d
```

### Run project

This project uses uv dependency manager, so dependencies are installed automatically on first run.

**Start the development server:**

```shell
make serve
```

**Start celery worker:**

```shell
make worker 
```

**Start celery beat:**

```shell
make beat
```

### Linting

```shell
make lint
```

### Run tests

```shell
make test
```
