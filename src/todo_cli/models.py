"""Todo list domain models and state transitions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated, ClassVar, NewType

from pydantic import BaseModel, ConfigDict, StringConstraints

TaskId = NewType("TaskId", str)
NonEmptyText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class Task(BaseModel):
    """A single persisted todo item."""

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True, extra="forbid")

    id: NonEmptyText
    title: NonEmptyText
    completed: bool = False


class TodoList(BaseModel):
    """The complete persisted todo state."""

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True, extra="forbid")

    tasks: tuple[Task, ...] = ()


@dataclass(frozen=True, slots=True)
class TaskNotFound:
    """An expected result when a task ID is absent."""

    task_id: TaskId


def add_task(todo_list: TodoList, task_id: TaskId, title: str) -> TodoList:
    """Return a todo list with one newly added task."""
    task = Task(id=task_id, title=title)
    return TodoList(tasks=(*todo_list.tasks, task))


def complete_task(todo_list: TodoList, task_id: TaskId) -> TodoList | TaskNotFound:
    """Return a todo list with the selected task marked complete."""
    if not any(task.id == task_id for task in todo_list.tasks):
        return TaskNotFound(task_id=task_id)
    return TodoList(
        tasks=tuple(
            task.model_copy(update={"completed": True}) if task.id == task_id else task
            for task in todo_list.tasks
        )
    )


def edit_task(
    todo_list: TodoList,
    task_id: TaskId,
    title: str,
) -> TodoList | TaskNotFound:
    """Return a todo list with the selected task title changed."""
    if not any(task.id == task_id for task in todo_list.tasks):
        return TaskNotFound(task_id=task_id)
    replacement = Task(id=task_id, title=title, completed=False)
    return TodoList(
        tasks=tuple(
            replacement.model_copy(update={"completed": task.completed})
            if task.id == task_id
            else task
            for task in todo_list.tasks
        )
    )


def delete_task(todo_list: TodoList, task_id: TaskId) -> TodoList | TaskNotFound:
    """Return a todo list without the selected task."""
    remaining = tuple(task for task in todo_list.tasks if task.id != task_id)
    if len(remaining) == len(todo_list.tasks):
        return TaskNotFound(task_id=task_id)
    return TodoList(tasks=remaining)
