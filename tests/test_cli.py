from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Final, TypedDict

from pydantic import TypeAdapter


class StoredTask(TypedDict):
    id: str
    title: str
    completed: bool


class StoredTodoList(TypedDict):
    tasks: list[StoredTask]


DATA_ADAPTER: Final = TypeAdapter(StoredTodoList)


def run_cli(project_root: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(project_root / "src")
    return subprocess.run(  # noqa: S603
        [sys.executable, "-m", "todo_cli", *arguments],
        cwd=project_root,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )


def read_data(data_file: Path) -> StoredTodoList:
    return DATA_ADAPTER.validate_json(data_file.read_bytes())


def add_fixture(project_root: Path, data_file: Path) -> str:
    result = run_cli(
        project_root,
        "add",
        "Write tests",
        "--data-file",
        str(data_file),
    )
    assert result.returncode == 0, result.stderr
    return read_data(data_file)["tasks"][0]["id"]


def test_add_persists_a_new_task(tmp_path: Path) -> None:
    # Given
    project_root = Path(__file__).parents[1]
    data_file = tmp_path / "tasks.json"

    # When
    result = run_cli(
        project_root,
        "add",
        "Write tests",
        "--data-file",
        str(data_file),
    )

    # Then
    assert result.returncode == 0, result.stderr
    task = read_data(data_file)["tasks"][0]
    assert task["title"] == "Write tests"
    assert task["completed"] is False
    assert task["id"] in result.stdout


def test_list_reads_a_task_in_a_new_process(tmp_path: Path) -> None:
    # Given
    project_root = Path(__file__).parents[1]
    data_file = tmp_path / "tasks.json"
    task_id = add_fixture(project_root, data_file)

    # When
    result = run_cli(project_root, "list", "--data-file", str(data_file))

    # Then
    assert result.returncode == 0, result.stderr
    assert task_id in result.stdout
    assert "Write tests" in result.stdout
    assert "pending" in result.stdout


def test_complete_persists_the_completed_state(tmp_path: Path) -> None:
    # Given
    project_root = Path(__file__).parents[1]
    data_file = tmp_path / "tasks.json"
    task_id = add_fixture(project_root, data_file)

    # When
    result = run_cli(
        project_root,
        "complete",
        task_id,
        "--data-file",
        str(data_file),
    )

    # Then
    assert result.returncode == 0, result.stderr
    assert read_data(data_file)["tasks"][0]["completed"] is True


def test_edit_persists_the_new_title(tmp_path: Path) -> None:
    # Given
    project_root = Path(__file__).parents[1]
    data_file = tmp_path / "tasks.json"
    task_id = add_fixture(project_root, data_file)

    # When
    result = run_cli(
        project_root,
        "edit",
        task_id,
        "Ship todo CLI",
        "--data-file",
        str(data_file),
    )

    # Then
    assert result.returncode == 0, result.stderr
    assert read_data(data_file)["tasks"][0]["title"] == "Ship todo CLI"


def test_delete_persists_removal(tmp_path: Path) -> None:
    # Given
    project_root = Path(__file__).parents[1]
    data_file = tmp_path / "tasks.json"
    task_id = add_fixture(project_root, data_file)

    # When
    result = run_cli(
        project_root,
        "delete",
        task_id,
        "--data-file",
        str(data_file),
    )

    # Then
    assert result.returncode == 0, result.stderr
    assert read_data(data_file) == {"tasks": []}


def test_unknown_task_exits_without_creating_data(tmp_path: Path) -> None:
    # Given
    project_root = Path(__file__).parents[1]
    data_file = tmp_path / "tasks.json"

    # When
    result = run_cli(
        project_root,
        "delete",
        "missing-id",
        "--data-file",
        str(data_file),
    )

    # Then
    assert result.returncode == 1
    assert "Task not found: missing-id" in result.stderr
    assert not data_file.exists()
