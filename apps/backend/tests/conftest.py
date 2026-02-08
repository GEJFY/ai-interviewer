"""Pytest configuration and fixtures."""

import sys
from pathlib import Path

# Add source directories to Python path
backend_src = Path(__file__).parent.parent / "src"
ai_src = Path(__file__).parent.parent.parent.parent / "packages" / "@grc" / "ai" / "src"
core_src = Path(__file__).parent.parent.parent.parent / "packages" / "@grc" / "core" / "src"

for path in [backend_src, ai_src, core_src]:
    if path.exists() and str(path) not in sys.path:
        sys.path.insert(0, str(path))
