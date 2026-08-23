"""JSON persistence for todo lists."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, override

from pydantic import ValidationError

from todo_cli.models import TodoList

if TYPE_CHECKING:
    from pathlib import Path


@dataclass(frozen=True, slots=True)
class InvalidDataFileError(Exception):
    """Raised when a persisted todo file does not match the schema."""

    path: Path

    @override
    def __str__(self) -> str:
        """Return the user-facing storage error."""
        return f"Invalid todo data file: {self.path}"


def load_tasks(path: Path) -> TodoList:
    """Load persisted tasks, returning an empty list for a new data file."""
    try:
        raw_data = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return TodoList()
    try:
        return TodoList.model_validate_json(raw_data)
    except ValidationError as error:
        raise InvalidDataFileError(path=path) from error


def save_tasks(path: Path, todo_list: TodoList) -> None:
    """Atomically persist the complete todo list as JSON."""
    _ = path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_name(f".{path.name}.tmp")
    _ = temporary_path.write_text(
        f"{todo_list.model_dump_json(indent=2)}\n",
        encoding="utf-8",
    )
    _ = temporary_path.replace(path)
