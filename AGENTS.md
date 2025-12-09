# Repository Guidelines

## Project Structure & Module Organization
- Core logic lives in `core/` (HTTP client, auth, persistence) with data models in `models/`. Shared helpers are in `utils/` (variable resolution, markdown parsing).
- Desktop UI widgets are under `ui/`; the Flask web UI, templates, and static assets are in `web/` (entrypoint `web/web_server.py`, default port `15555`).
- Sample and shared projects sit in `projects/` and `shared_projects/`; `.lumina_data/` is created at runtime for session keys and cached data. Main launchers: `main.py`, `run.sh`, `web_server_standalone.py`, and `web_server_persistent.py`.
- Root `test_*.py` scripts cover concurrency and Playwright-based UI checks; keep new tests alongside these unless tightly coupled to a module.

## Setup, Build, and Development Commands
- Install deps: `pip install -r requirements.txt` (add `pip install playwright` + `playwright install chromium` if running UI tests).
- Desktop app: `python main.py` (or `./run.sh`) launches the PyQt UI.
- Web app: `python web/web_server.py` serves the browser UI at `http://localhost:15555`; use `web_server_persistent.py` to enable auto-save into `projects/`.
- Quick API smoke: run `python sample_api.md` examples through the UI; for manual HTTP calls, `web/http_client.py` is the reference.

## Testing Guidelines
- Concurrency/regression: `python test_concurrency.py` (no server needed).
- Web UI sanity: `python test_ui_buttons.py`, `python test_button_clicks.py`, or `python test_send_response.py` with the web server running on `15555`; screenshots land under `/tmp/`.
- Name tests `test_<feature>.py`; prefer deterministic assertions over printouts when extending coverage.

## Coding Style & Naming Conventions
- Python 3.7+ with 4-space indentation, snake_case functions, PascalCase classes, and UPPER_SNAKE constants. Keep type hints and docstrings consistent with existing files.
- Favor f-strings, early returns, and thread-safe patterns already used in `core/project_manager.py`. When touching UI, preserve existing DOM IDs/classes (`btn-*`) used by Playwright tests.
- Keep Markdown/docs concise; inline comments only for non-obvious logic.

## Commit & Pull Request Guidelines
- Follow the existing log style: `<type>: <summary>` (e.g., `feat: add share import`, `fix: insomnia import error`); use present tense and keep scope small.
- PRs should include a short description, relevant issue/bug link, impacted UI notes, and before/after screenshots for visible changes. List commands/tests executed (e.g., web server + specific `test_*.py` runs).
- Avoid committing generated artifacts or temporary screenshots; clean `/tmp` outputs and local project exports before submission.

## 추가 커뮤니케이션 및 커밋 규칙
- 모든 주고받는 답변은 한글로 진행한다.
- 모든 작업이 끝난 후에, 수정한 파일에 한정하여 커밋을 진행한다. 
- 커밋 메시지는 한글로 작성한다.
- 커밋 메시지에는 유형별 접두어를 붙인다.
  - 새로운 기능: `feat :`
  - 에러 수정: `fix :`
  - 리팩토링: `refactor :`
  - 문서 수정: `docs :`
