# todo-cli

JSON 파일 하나에 할 일을 저장하는 작은 커맨드라인 할 일 관리 도구입니다.

> [homelab](https://github.com/cynkai/homelab)과 이어지는 레포입니다.
> homelab 레포로 홈랩 서버(MSI GP73)를 먼저 구축하고, 구축이 끝나면 이 레포를 바탕으로 다음 작업을 이어갈 예정입니다.

## 특징

- `add`, `list`, `complete`, `edit`, `delete` 다섯 가지 명령
- 데이터는 `tasks.json` 한 파일에 저장 (`--data-file`로 경로 변경 가능)
- 임시 파일에 먼저 쓰고 교체하는 방식으로 저장해, 쓰는 도중 끊겨도 파일이 깨지지 않음
- 같은 데이터 파일을 여러 프로세스가 수정하면 파일 잠금으로 작업을 순서대로 처리
- Pydantic으로 저장 파일의 스키마를 검증하고, 빈 제목은 거부
- ruff(전체 룰), basedpyright(strict), pytest로 품질 관리

## 설치

Python 3.12 이상과 [uv](https://docs.astral.sh/uv/)가 필요합니다.

```bash
git clone https://github.com/cynkai/todo-cli.git
cd todo-cli
uv sync
```

## 사용법

```bash
uv run todo add "장보기"
uv run todo list
uv run todo complete <task-id>
uv run todo edit <task-id> "장보기 (우유, 계란)"
uv run todo delete <task-id>
```

`list`는 `ID [상태] 제목` 형식으로 출력합니다. 다른 파일에 저장하려면 `--data-file`을 붙입니다.

```bash
uv run todo list --data-file ~/notes/tasks.json
```

같은 파일의 수정 명령은 데이터 파일 옆의 잠금 파일(예: `.tasks.json.lock`)을 공유합니다. 수정 중에는 잠금 파일을 그대로 두세요. 운영체제가 종료된 프로세스의 잠금을 해제합니다.

## 개발

```bash
uv run pytest
uv run ruff check .
uv run basedpyright
```

## 구조

| 파일 | 하는 일 |
| --- | --- |
| `src/todo_cli/models.py` | 할 일 모델과 추가·완료·수정·삭제 로직 |
| `src/todo_cli/storage.py` | JSON 파일 읽기·저장 |
| `src/todo_cli/cli.py` | Typer 기반 명령어 |
| `tests/test_cli.py` | CLI 테스트 |
