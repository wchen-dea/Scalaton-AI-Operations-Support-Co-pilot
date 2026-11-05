"""Module entrypoint: `python -m app` binds the Databricks-injected port.

Databricks Apps inject `DATABRICKS_APP_PORT`; the app must bind to it (never a
hardcoded port). This entrypoint reads it and starts uvicorn.
"""

from __future__ import annotations

import os

import uvicorn


def main() -> None:
    port = int(os.environ.get("DATABRICKS_APP_PORT", "8000"))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
