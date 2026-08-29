import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from api.config import environment


@lru_cache
def load_catalog() -> dict[str, Any]:
    with Path(environment.detector.catalog_path).open() as f:
        return json.load(f)
