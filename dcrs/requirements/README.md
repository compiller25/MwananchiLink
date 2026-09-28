# requirements/

Python dependency files split by environment.

## Files

### `base.txt` — production dependencies

```
Django>=5.0,<5.3   # Web framework
Pillow>=10         # Image processing for citizen profile photos
python-dotenv>=1.0 # Loads .env into os.environ
requests>=2.31     # HTTP client used to call the SendAfrica SMS API
```

### `development.txt` — development dependencies

Includes everything in `base.txt` via `-r base.txt`, plus any dev-only packages (linters, test runners, debug tools) as they are added.

## Installing

```bash
# Development (recommended for local work)
pip install -r requirements/development.txt

# Production only
pip install -r requirements/base.txt
```

## Adding PostgreSQL support

```bash
pip install psycopg2-binary
```

Add `psycopg2-binary` to `requirements/base.txt` when targeting a PostgreSQL production server.

## SMS gateway — already live

`requests` (above) is all that's needed — `apps/notifications/services.py` calls the **SendAfrica** REST API directly over plain HTTPS, no dedicated SDK required. Set `SENDAFRICA_API_KEY` in `.env` to switch from the internal simulator to real sends; see `apps/notifications/README.md` for the full integration details.
