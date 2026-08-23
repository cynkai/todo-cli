"""Command-line interface for the todo manager."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Final, assert_never
from uuid import uuid4

import typer
from pydantic import ValidationError

from todo_cli.models import (
    TaskId,
    TaskNotFound,
    TodoList,
    add_task,
    complete_task,
    delete_task,
    edit_task,
)
from todo_cli.storage import load_tasks, save_tasks

DEFAULT_DATA_FILE: Final = Path("tasks.json")
DataFileOption = Annotated[
    Path,
    typer.Option("--data-file", help="Path to the JSON data file."),
]
TaskIdArgument = Annotated[str, typer.Argument(help="ID of the task.")]
TitleArgument = Annotated[str, typer.Argument(help="Task title.")]

app = typer.Typer(help="Manage a JSON-backed todo list.", no_args_is_help=True)


def _report_not_found(result: TaskNotFound) -> None:
    typer.echo(f"Task not found: {result.task_id}", err=True)
    raise typer.Exit(code=1)


@app.command()
def add(
    title: TitleArgument,
    data_file: DataFileOption = DEFAULT_DATA_FILE,
) -> None:
    """Add a task."""
    try:
        updated = add_task(load_tasks(data_file), TaskId(str(uuid4())), title)
    except ValidationError as error:
        typer.echo(f"Invalid task title: {error.errors()[0]['msg']}", err=True)
        raise typer.Exit(code=2) from error
    save_tasks(data_file, updated)
    typer.echo(f"Added: {updated.tasks[-1].id}")


@app.command("list")
def list_tasks(data_file: DataFileOption = DEFAULT_DATA_FILE) -> None:
    """List all tasks."""
    todo_list = load_tasks(data_file)
    if not todo_list.tasks:
        typer.echo("No tasks.")
        return
    for task in todo_list.tasks:
        status = "completed" if task.completed else "pending"
        typer.echo(f"{task.id}\t[{status}]\t{task.title}")


@app.command()
def complete(
    task_id: TaskIdArgument,
    data_file: DataFileOption = DEFAULT_DATA_FILE,
) -> None:
    """Mark a task complete."""
    result = complete_task(load_tasks(data_file), TaskId(task_id))
    match result:
        case TodoList():
            save_tasks(data_file, result)
            typer.echo(f"Completed: {task_id}")
        case TaskNotFound():
            _report_not_found(result)
        case unreachable:
            assert_never(unreachable)


@app.command()
def edit(
    task_id: TaskIdArgument,
    title: TitleArgument,
    data_file: DataFileOption = DEFAULT_DATA_FILE,
) -> None:
    """Change a task title."""
    try:
        result = edit_task(load_tasks(data_file), TaskId(task_id), title)
    except ValidationError as error:
        typer.echo(f"Invalid task title: {error.errors()[0]['msg']}", err=True)
        raise typer.Exit(code=2) from error
    match result:
        case TodoList():
            save_tasks(data_file, result)
            typer.echo(f"Updated: {task_id}")
        case TaskNotFound():
            _report_not_found(result)
        case unreachable:
            assert_never(unreachable)


@app.command()
def delete(
    task_id: TaskIdArgument,
    data_file: DataFileOption = DEFAULT_DATA_FILE,
) -> None:
    """Delete a task."""
    result = delete_task(load_tasks(data_file), TaskId(task_id))
    match result:
        case TodoList():
            save_tasks(data_file, result)
            typer.echo(f"Deleted: {task_id}")
        case TaskNotFound():
            _report_not_found(result)
        case unreachable:
            assert_never(unreachable)
