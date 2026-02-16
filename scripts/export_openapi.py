#!/usr/bin/env python3
"""Export OpenAPI specification from the FastAPI application.

Usage:
    python scripts/export_openapi.py              # stdout
    python scripts/export_openapi.py -o docs/openapi.json
"""

import argparse
import json
import os
import sys

# Ensure the app can be imported without real env vars
os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("SECRET_KEY", "openapi-export-dummy-key")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///dummy.db")

# Add source paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "apps", "backend", "src"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "packages", "@grc", "core", "src"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "packages", "@grc", "ai", "src"))


def main():
    parser = argparse.ArgumentParser(description="Export OpenAPI spec")
    parser.add_argument("-o", "--output", help="Output file path (default: stdout)")
    args = parser.parse_args()

    from grc_backend.main import create_app

    app = create_app()
    spec = app.openapi()

    content = json.dumps(spec, indent=2, ensure_ascii=False)

    if args.output:
        os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(content)
            f.write("\n")
        print(f"OpenAPI spec written to {args.output}", file=sys.stderr)
    else:
        print(content)


if __name__ == "__main__":
    main()
