# Promotions Service

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/Language-Python-blue.svg)](https://python.org/)
[![CI](https://github.com/CSCI-GA-2820-SU26-001/promotions/actions/workflows/ci.yml/badge.svg)](https://github.com/CSCI-GA-2820-SU26-001/promotions/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/CSCI-GA-2820-SU26-001/promotions/branch/master/graph/badge.svg)](https://codecov.io/gh/CSCI-GA-2820-SU26-001/promotions)

The Promotions service is a RESTful Flask microservice for managing product and store promotions in an eCommerce application. A promotion represents a special sale or offer, such as "buy 1 get 1 free", a fixed dollar discount, or a percentage discount.

The CI badge reports whether the current GitHub Actions test and lint workflow is passing. Click the badge to inspect failing checks and test output.

## Resource Model

Promotion records are stored in PostgreSQL and include:

| Field | Type | Description |
| --- | --- | --- |
| `id` | integer | Unique promotion identifier |
| `name` | string | Promotion name |
| `promotion_type` | enum | One of `UNKNOWN`, `PERCENT_OFF`, `FIXED_AMOUNT`, `BOGO` |
| `discount_value` | decimal | Discount amount or percentage value |
| `start_date` | date | Date the promotion starts |
| `end_date` | date | Date the promotion ends |

Example JSON payload:

```json
{
  "name": "Summer Sale",
  "promotion_type": "PERCENT_OFF",
  "discount_value": "20.00",
  "start_date": "2026-06-01",
  "end_date": "2026-06-07"
}
```

## REST API

The REST API is served under the `/api` prefix and documented with Swagger. Interactive documentation is available at `/apidocs/`, and the raw OpenAPI spec at `/api/swagger.json`.

| Method | Endpoint | Description | Request Body |
| --- | --- | --- | --- |
| `GET` | `/` | Admin UI for the service | None |
| `GET` | `/health` | Health check for Kubernetes probes | None |
| `GET` | `/apidocs/` | Swagger UI documentation | None |
| `POST` | `/api/promotions` | Create a promotion | Promotion JSON |
| `GET` | `/api/promotions` | List promotions (filter by `name` or `promotion_type`) | None |
| `GET` | `/api/promotions/<id>` | Read a promotion by ID | None |
| `PUT` | `/api/promotions/<id>` | Update a promotion by ID | Promotion JSON |
| `DELETE` | `/api/promotions/<id>` | Delete a promotion by ID | None |
| `PUT` | `/api/promotions/<id>/deactivate` | Deactivate a promotion | None |

All API responses, including error responses, should be returned as JSON except successful `DELETE` responses, which return `204 No Content`.

## Development Setup

The recommended setup is the VS Code Dev Container provided with the course project. Open the repository in VS Code and reopen it in the container when prompted.

For local setup, install the project dependencies:

```bash
make install
```

Copy the example environment file if needed:

```bash
cp dot-env-example .env
```

## Repository Structure

```text
service/
├── models.py             # Promotion model and database access methods
├── routes.py             # Flask REST API routes
└── common/               # Shared status codes, error handlers, logging, and CLI commands

tests/
├── factories.py          # Test data factories
├── test_models.py        # Model unit tests
├── test_routes.py        # REST API route tests
└── test_cli_commands.py  # CLI command tests
```

## Running the Service

Start the service locally:

```bash
honcho start
```

Then open:

```text
http://localhost:8080/
```

## Running Tests

Run the full test suite:

```bash
make test
```

Run the linter:

```bash
make lint
```

The project goal is at least 95% test coverage.

## Expected JSON Input

`POST /promotions` and `PUT /promotions/<id>` expect a JSON body with these fields:

| Field | Required | Example |
| --- | --- | --- |
| `name` | Yes | `"Summer Sale"` |
| `promotion_type` | Yes | `"PERCENT_OFF"` |
| `discount_value` | No | `"20.00"` |
| `start_date` | No | `"2026-06-01"` |
| `end_date` | No | `"2026-06-07"` |

## Project Workflow

All work should be done on feature branches. Open a pull request for each user story, connect the PR to the matching ZenHub issue, and request review from another squad member before merging.
