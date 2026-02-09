"""Test configuration for grc_ai package."""

import sys
from pathlib import Path

# パッケージソースをパスに追加
ai_src = Path(__file__).parent.parent / "src"
if ai_src.exists() and str(ai_src) not in sys.path:
    sys.path.insert(0, str(ai_src))
