"""确保 `scripts` 包在测试导入路径中（将项目根加入 sys.path）。"""

import sys
from pathlib import Path

_ROOT = str(Path(__file__).resolve().parent.parent)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
