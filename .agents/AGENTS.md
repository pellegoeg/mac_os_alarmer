# Agent Rules & Guidelines for mac_os_alarmer

Welcome to the `mac_os_alarmer` codebase. This project runs modular background checks (e.g. PostgreSQL query checks, API checks) on macOS and sends alerts using macOS system notifications or Microsoft Teams hooks.

## Environment & Dependency Management
- **Tooling**: This project uses `uv` for python dependency and environment management.
- **Python Version**: Python >= 3.10 is required.
- **Formatting & Linting**: We use `ruff` for code linting and formatting. Always format files using `uv run ruff format` and check code with `uv run ruff check` before committing.
  - Line-length is 88.
  - Double quotes are preferred for strings.
  - Selected lints: E, F, I, UP, B.

## Adding New Features
### 1. Adding Checks
- All check types must inherit from `BaseCheck` in [checks.py](ac_os_alarmer/checks.py).
- Override the `run()` method to return a `CheckResult`.
- Ensure exceptions inside the checks are handled gracefully and return a `CheckResult` notifying the user about the check failure.

### 2. Adding Notifiers
- All notification channels must inherit from `BaseNotifier` in [notifiers.py](mac_os_alarmer/notifiers.py).
- Override the `notify()` method to perform the notification action.

## Configuration & Credentials
- **Local Config**: Configuration is stored in `config.json`. Do not commit actual database credentials or webhook URLs.
- **Secrets Management**: Use the `.env` file (copied from `.env.example`) to store secret keys, tokens, or database passwords. These are read via `dotenv`.
- Ensure new parameters are added to both `config.json.example` and `.env.example` if applicable.

## Testing & Verification
- **Test Suite**: Run `uv run pytest` to execute current tests (e.g. `uv run pytest test_alert.py`).
- Add tests for new checks or notifier classes.

## LaunchAgent & Background Execution
- The program runs in the background using a macOS LaunchAgent.
- When you update dependencies or make critical modifications to how `main.py` is invoked, you may need to run `./install_launchagent.sh` to update/re-register the LaunchAgent.
- Logs can be inspected at:
  - `~/Library/Logs/com.user.mac_os_alarmer.stdout.log`
  - `~/Library/Logs/com.user.mac_os_alarmer.stderr.log`
