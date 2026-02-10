"""Test configuration for grc_core package."""

import sys
from pathlib import Path

# パッケージソースをパスに追加
core_src = Path(__file__).parent.parent / "src"
if core_src.exists() and str(core_src) not in sys.path:
    sys.path.insert(0, str(core_src))
