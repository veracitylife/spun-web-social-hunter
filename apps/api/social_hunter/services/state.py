import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from social_hunter.config import get_settings


class PersistentState:
    def __init__(self, path: str | None = None) -> None:
        configured = path or get_settings().state_file_path
        self.path = Path(configured)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.data: dict[str, Any] = self._load()

    def _load(self) -> dict[str, Any]:
        if not self.path.exists():
            return {}
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}

    def save(self) -> None:
        temp = self.path.with_suffix(self.path.suffix + ".tmp")
        temp.write_text(json.dumps(self.data, indent=2, sort_keys=True), encoding="utf-8")
        temp.replace(self.path)

    def get(self, key: str, default: Any) -> Any:
        return self.data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self.data[key] = value
        self.save()


def dump_model(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if isinstance(value, list):
        return [dump_model(item) for item in value]
    if isinstance(value, dict):
        return {key: dump_model(item) for key, item in value.items()}
    return value
