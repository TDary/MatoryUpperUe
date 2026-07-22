# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-07-22

### Added

- Initial release of MatoryUpperUe framework
- TCP protocol layer with JSON codec and stream buffering (`Connection`)
- Widget element model with query and interaction methods (`Widget`, `ButtonWidget`, `TextWidget`)
- Page Object pattern with `WidgetDescriptor` lazy binding
- `Session` manager with multi-connection registry
- `Recorder` for intercepting operations and generating pytest test code
- pytest plugin with `session` / `sessions` fixtures and CLI options
- File logging support (`log_file` / `log_level` params, `--matory-log-file` / `--matory-log-level` CLI)
- `Session.start_health_check()` / `stop_health_check()` for background liveness monitoring
- `Session.add_send_hook()` / `remove_send_hook()` middleware mechanism
- `Page.invalidate_widgets()` for cache busting on connection change
- `__version__` exported from `importlib.metadata`
- Thread-safe request ID generation and `Connection.send_and_recv()`
- Auto-reconnect with configurable retry count and delay
- MIT License

### Changed

- **BREAKING**: Renamed `ConnectionError` to `MatoryConnectionError` to avoid shadowing Python's builtin `ConnectionError`. Update any `except ConnectionError` or `from matory.errors import ConnectionError` references.
- `Session.close()` is now thread-safe with `_closed` flag and lock protection
- `WidgetDescriptor` now rejects unknown keyword arguments (raises `TypeError` on typos)
- `find_text()` now requires at least one of `keyword`, `id`, or `name` (previously sent empty request)
- `find_text()` `WidgetNotFoundError` now reports the actual locator used instead of hardcoded "keyword"
- `wait_until` (Session and Widget) now catches only `(MatoryError, OSError)` instead of all exceptions
- `decode_response` now wraps malformed JSON in `MatoryError` instead of raw `json.JSONDecodeError`
- `Recorder` now uses Session's send-hook mechanism instead of monkey-patching `_send_cmd`
- `Connection.close()` no longer holds the lock, allowing it to interrupt blocked `send_and_recv` calls
- `_recv_line_unlocked` now limits reconnection attempts per call (prevents infinite loops)
- File logging dedup now checks specific file path (allows multiple log files)

### Fixed

- README `widget.name` corrected to `widget.get_name()`
- `lobby_page.py` missing `enter_room()` method added
