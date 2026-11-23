"""JSON persistence for todo lists."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import TYPE_CHECKING, override

from filelock import FileLock
from pydantic import ValidationError

from todo_cli.models import TaskNotFound, TodoList

if TYPE_CHECKING:
    from collections.abc import Callable


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
    except UnicodeDecodeError as error:
        raise InvalidDataFileError(path=path) from error
    try:
        return TodoList.model_validate_json(raw_data)
    except ValidationError as error:
        raise InvalidDataFileError(path=path) from error


def update_tasks[Result: TodoList | TaskNotFound](
    path: Path,
    change: Callable[[TodoList], Result],
) -> Result:
    """Lock the read, change and save as one transaction across CLI processes."""
    path = path.resolve()
    _ = path.parent.mkdir(parents=True, exist_ok=True)
    with FileLock(path.with_name(f".{path.name}.lock")):
        result = change(load_tasks(path))
        if isinstance(result, TodoList):
            _save_tasks(path, result)
        return result


def _save_tasks(path: Path, todo_list: TodoList) -> None:
    temporary_path: Path | None = None
    try:
        with NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary_path = Path(handle.name)
            _ = handle.write(f"{todo_list.model_dump_json(indent=2)}\n")
        _ = temporary_path.replace(path)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
