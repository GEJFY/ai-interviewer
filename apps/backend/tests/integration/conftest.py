"""Pytest configuration for integration tests."""

import sys
from pathlib import Path

# Add source directories to Python path
project_root = Path(__file__).parent.parent.parent.parent.parent
backend_src = Path(__file__).parent.parent.parent / "src"
ai_src = project_root / "packages" / "@grc" / "ai" / "src"
core_src = project_root / "packages" / "@grc" / "core" / "src"
infrastructure_src = project_root / "packages" / "@grc" / "infrastructure" / "src"

for path in [backend_src, ai_src, core_src, infrastructure_src]:
    if path.exists():
        sys.path.insert(0, str(path))
