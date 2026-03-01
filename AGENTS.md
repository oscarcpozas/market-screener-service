# Development Guide

## Codebase Structure

- [README](README.md) - general information about how projects work

## Commands

- Environment:
    - Start dependencies necessary to run the project: `docker compose up -d`
    - Apply Flyway migration: `make flyway-migrate`
- Build/Serve:
    - Start FastAPI Uvicorn server: `make serve`
    - Start Celery worker: `make worker`
    - Start Celery scheduler (beat): `make beat`
- Tests:
    - All tests: `make test`
    - Single test: `pytest path/to/test.py::TestClass::test_method`
- Lint:
    - `make lint`

## Commits and Pull Requests

Use [conventional commits](https://www.conventionalcommits.org/en/v1.0.0/) for all commit messages and PR titles.

### Commit types

- `feat`: New feature or functionality (touches production code)
- `fix`: Bug fix (touches production code)
- `chore`: Non-production changes (docs, tests, config, CI, refactoring agents instructions, etc.)

### Format

```text
<type>(<scope>): <description>
```

Examples:

- `feat(insights): add retention graph export`
- `fix(cohorts): handle empty cohort in query builder`
- `chore(ci): update GitHub Actions workflow`
- `chore: update AGENTS.md instructions`

### Rules

- Scope is optional but encouraged when the change is specific to a feature area
- Description should be lowercase and not end with a period
- Keep the first line under 72 characters

## Security

### SQL Security

- **Never** use f-strings with user-controlled values in SQL queries - this creates SQL injection vulnerabilities
- Use parameterized queries for all VALUES: `cursor.execute("SELECT * FROM t WHERE id = %s", [id])`
- Table/column names from Django ORM metadata (`model._meta.db_table`) are trusted sources
- When raw SQL is necessary with dynamic table/column names:

```python
  # Build query string separately from execution, document why identifiers are safe
  table = model._meta.db_table  # Trusted: from Django ORM metadata
  query = f"SELECT COUNT(*) FROM {table} WHERE team_id = %s"
  cursor.execute(query, [team_id])  # Values always parameterized
```

**Sanitizers** (for use in placeholders):

- `ast.Constant(value=...)` - wraps values safely
- `ast.Tuple(exprs=...)` - for lists of values

## Architecture guidelines

- Inside src/ exists folders by context (DDD style)
- Every context follows hexagonal architecture for responsability separation

## Important rules for Code Style

- Python: Use type hints, follow mypy strict rules
- Error handling: Prefer explicit error handling with typed errors
- Naming: Use descriptive names and snake_case for Python
- Comments: should not duplicate the code below, don't tell me "this finds the shortest username" tell me _why_ that is
  important, if it isn't important don't add a comment, almost never add a comment
- Python tests: do not add doc comments
- any tests: prefer to use parameterized tests, think carefully about what input and output look like so that the tests
  exercise the system and explain the code to the future traveller
- Python tests: in python use the parameterized library for parameterized tests, every time you are tempted to add more
  than one assertion to a test consider (really carefully) if it should be a parameterized test instead
- always remember that there is a tension between having the fewest parts to code (a simple system) and having the most
  understandable code (a maintainable system). structure code to balance these two things.
- Separation of concerns: Keep different responsibilities in different places (data/logic/presentation, safety
  checks/policies, etc.)
- Reduce nesting: Use early returns, guard clauses, and helper methods to avoid deeply nested code
- Avoid over-engineering: Don't apply design patterns just because you know them
- Start simple, iterate: Build minimal solution first, add complexity only when demanded

## General

- Markdown: prefer semantic line breaks; no hard wrapping
