# motaby-client

Python client library for the [MOTABY](https://motaby.de) motor disorder assessment platform.

`motaby-client` lets research tools and pipelines (MOTABY-Statistics, MOTABY-ML, etc.)
authenticate against a MOTABY backend using an API key and programmatically read
assessments, patients, and batteries.

## Requirements

- Python 3.9 or newer
- A MOTABY practitioner account with an active API key (see [Getting an API Key](#getting-an-api-key))

## Installation

```bash
pip install motaby-client
```

With optional pandas support for DataFrame export:

```bash
pip install "motaby-client[pandas]"
```

## Quick Start

```python
from motaby import MOTABYClient

client = MOTABYClient(
    base_url="https://motaby.de",
    api_key="mby_your_api_key_here",
)

# Check connectivity
if not client.ping():
    raise RuntimeError("Cannot reach MOTABY server")

# List assessments for a patient (paginated)
page = client.assessments.list(patient_id="P001", code="spiral-drawing")
for assessment in page:
    print(assessment.assessment_code, assessment.created_at)

# Fetch all pages automatically
all_assessments = client.assessments.list_all(patient_id="P001")

# Load as a pandas DataFrame (requires the pandas extra)
df = client.assessments.to_dataframe(patient_id="P001")
print(df.head())

# Use as a context manager for automatic cleanup
with MOTABYClient(base_url="https://motaby.de", api_key="mby_...") as client:
    patients = client.patients.list_all()
    batteries = client.batteries.list_all()
```

## Endpoint Reference

### `client.assessments`

| Method | Signature | Description |
|--------|-----------|-------------|
| `list` | `list(patient_id, code, status, date_from, date_to, page, page_size)` | Fetch one page of assessments. Returns `PaginatedResponse[Assessment]`. |
| `list_all` | `list_all(patient_id, code, status, date_from, date_to)` | Auto-paginate and return all matching `Assessment` objects. |
| `get` | `get(assessment_id: str)` | Fetch a single assessment by UUID. Returns `Assessment`. |
| `to_dataframe` | `to_dataframe(patient_id, code, status, date_from, date_to)` | Return all matching assessments as a `pandas.DataFrame`. Requires the `pandas` extra. |

**Assessment fields:**

```python
assessment.id                  # UUID
assessment.patient_id          # Pseudonymized patient identifier
assessment.assessment_code     # e.g. "spiral-drawing", "finger-tapping"
assessment.assessment_type     # e.g. "drawing", "video"
assessment.status              # "preliminary" | "final"
assessment.data                # dict — raw assessment payload
assessment.configuration       # dict — test configuration (e.g. hand used)
assessment.effective_datetime  # datetime or None
assessment.created_at          # datetime
assessment.notes               # Optional free-text notes
assessment.study               # Optional study/cohort identifier
assessment.media_count         # Number of attached media files
assessment.media_items         # List[MediaItem] — metadata only
```

### `client.patients`

| Method | Signature | Description |
|--------|-----------|-------------|
| `list` | `list(page=1, page_size=50)` | Fetch one page of patients. Returns `PaginatedResponse[Patient]`. |
| `list_all` | `list_all()` | Auto-paginate and return all `Patient` objects. |
| `to_dataframe` | `to_dataframe()` | Return all patients as a `pandas.DataFrame`. Requires the `pandas` extra. |

**Patient fields:**

```python
patient.patient_id           # Pseudonymized patient identifier
patient.assessment_count     # Total number of assessments recorded
patient.latest_assessment_at # datetime of most recent assessment, or None
```

### `client.batteries`

| Method | Signature | Description |
|--------|-----------|-------------|
| `list` | `list(page=1, page_size=50)` | Fetch one page of batteries. Returns `PaginatedResponse[Battery]`. |
| `list_all` | `list_all()` | Auto-paginate and return all `Battery` objects. |
| `to_dataframe` | `to_dataframe()` | Return all batteries as a `pandas.DataFrame`. Requires the `pandas` extra. |

**Battery fields:**

```python
battery.id           # UUID
battery.name         # Display name
battery.description  # Optional description
battery.color        # Optional hex colour string
battery.active       # bool — whether the battery is active
battery.created_at   # datetime or None
```

### `client.ping()`

Returns `True` if the server is reachable, `False` otherwise. Useful for health checks.

## Error Handling

All errors raised by the client are subclasses of `MOTABYError`.

```python
from motaby import (
    MOTABYClient,
    MOTABYError,
    AuthenticationError,  # 401 — invalid or expired API key
    AuthorizationError,   # 403 — insufficient permissions
    NotFoundError,        # 404 — resource not found
    ValidationError,      # 422 — invalid request parameters
    RateLimitError,       # 429 — too many requests; e.retry_after gives wait time in seconds
    ServerError,          # 5xx — server-side error
)

client = MOTABYClient(base_url="...", api_key="mby_...")

try:
    assessment = client.assessments.get("non-existent-uuid")
except NotFoundError:
    print("Assessment not found")
except AuthenticationError:
    print("Check your API key — it may have expired")
except RateLimitError as e:
    print(f"Rate limited. Retry after {e.retry_after}s")
except MOTABYError as e:
    print(f"Unexpected error: {e}")
```

The client automatically retries transient server errors and rate-limit responses with
exponential back-off (up to `max_retries`, default 3).

## Getting an API Key

API keys are managed directly in the MOTABY mobile app:

1. Open the MOTABY app and log in with your practitioner account.
2. Navigate to **Settings → API Keys**.
3. Tap **+**, enter a descriptive name (e.g. `research-laptop`), and choose an expiry
   duration (1 h, 4 h, 8 h, or 24 h).
4. The key is shown **exactly once** — copy it immediately and store it securely.
5. Pass the key to the client as `api_key="mby_..."`. All keys start with `mby_`.

Keys can be revoked at any time from the same screen by long-pressing a key card.

> **Note:** API keys grant read-only access to data owned by the practitioner who created
> them. They cannot create assessments, modify patients, or access other users' data.

## Development Setup

```bash
git clone https://github.com/DZNE-ataxia-research/MOTABY-client.git
cd MOTABY-client

python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -e ".[dev]"
```

### Running the tests

```bash
pytest tests/ -v
```

All tests use mocked HTTP responses — no live MOTABY server is needed.

### Type checking

```bash
mypy src/
```

### Project layout

```
src/motaby/
    __init__.py          # Public API — MOTABYClient + exception re-exports
    client.py            # MOTABYClient entry point
    _http.py             # Internal HTTP client (httpx, retry logic, error mapping)
    models.py            # Dataclasses: Assessment, Patient, Battery, MediaItem
    pagination.py        # PaginatedResponse[T] and PaginationMeta
    exceptions.py        # Exception hierarchy
    endpoints/
        assessments.py   # AssessmentsEndpoint
        patients.py      # PatientsEndpoint
        batteries.py     # BatteriesEndpoint
tests/
    conftest.py
    test_assessments.py
    test_patients.py
    test_batteries.py
    test_client.py
    test_pagination.py
```

## License

MIT
