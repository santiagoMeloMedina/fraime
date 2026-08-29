import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from api.config import environment


@lru_cache
def load_rules() -> dict[str, Any]:
    with Path(environment.prompt.rules_path).open() as f:
        return json.load(f)
