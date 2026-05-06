import pathlib
import sys


REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"

# Ensure both import styles work:
# - from src.utils.bbox import BBox
# - from utils.logger import get_logger
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(SRC_ROOT))
