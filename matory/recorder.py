"""Recorder — intercepts Widget operations and generates pytest test code."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from matory.session import Session


@dataclass
class Step:
    """A single recorded widget action."""

    action: str
    method: str
    value: str
    args: dict[str, Any] = field(default_factory=dict)
    connection: str | None = None


# Maps server command names to human-friendly action names
_INTERACTION_CMDS: dict[str, str] = {
    "ClickWidget": "click",
    "PressWidget": "press",
    "ReleaseWidget": "release",
    "SetWidgetEnabled": "set_enabled",
}


class Recorder:
    """Wraps a Session to record widget interactions for code generation.

    Uses Session's send-hook mechanism (``add_send_hook`` /
    ``remove_send_hook``) to intercept commands without monkey-patching,
    so multiple Recorders can coexist safely and the interception is
    robust against ``_send_cmd`` signature changes.

    Usage::

        rec = Recorder(session)
        rec.start()
        btn.click()           # recorded
        rec.stop()
        rec.generate_code("MyPage", "tests/test_my_page.py")
    """

    def __init__(self, session: Session) -> None:
        self._session = session
        self._steps: list[Step] = []
        self._recording = False
        self._hook = self._on_send

    @property
    def steps(self) -> list[Step]:
        """The list of recorded steps."""
        return self._steps

    def _on_send(self, cmd: str, args: dict[str, Any], connection: str | None) -> None:
        """Send-hook callback: record interaction commands."""
        if cmd in _INTERACTION_CMDS and self._recording:
            action = _INTERACTION_CMDS[cmd]
            method = args.get("method", "")
            value = args.get("value", "")
            step = Step(
                action=action,
                method=method,
                value=value,
                args=args,
                connection=connection,
            )
            self._steps.append(step)

    def start(self) -> None:
        """Start recording widget interactions.

        If already recording, this is a no-op.
        """
        if self._recording:
            return
        self._recording = True
        self._steps.clear()
        self._session.add_send_hook(self._hook)

    def stop(self) -> None:
        """Stop recording and unregister the send hook."""
        self._recording = False
        self._session.remove_send_hook(self._hook)

    def render_code(self, class_name: str) -> str:
        """Render generated pytest test code as a string.

        Widgets with the same (method, value) are deduplicated into a single
        Page Object descriptor.
        """
        # Deduplicate widgets, also track per-widget connection
        seen_widgets: dict[tuple[str, str], str] = {}  # (method, value) -> attr_name
        widget_connections: dict[tuple[str, str], str | None] = {}  # (method, value) -> connection
        attr_counter: dict[str, int] = {}

        for step in self._steps:
            key = (step.method, step.value)
            if key not in seen_widgets:
                # Generate a Python-safe attribute name
                safe_name = step.value.replace(" ", "_").replace("/", "_")
                if not safe_name.isidentifier():
                    safe_name = f"widget_{safe_name.replace('-', '_')}"
                if safe_name in attr_counter:
                    attr_counter[safe_name] += 1
                    safe_name = f"{safe_name}_{attr_counter[safe_name]}"
                else:
                    attr_counter[safe_name] = 0
                seen_widgets[key] = safe_name
                widget_connections[key] = step.connection

        # Build Page class
        descriptor_lines = []
        for (method, value), attr_name in seen_widgets.items():
            conn = widget_connections[(method, value)]
            if conn is not None:
                descriptor_lines.append(
                    f'    {attr_name} = WidgetDescriptor({method}="{value}", connection="{conn}")'
                )
            else:
                descriptor_lines.append(
                    f'    {attr_name} = WidgetDescriptor({method}="{value}")'
                )

        # Build test body
        action_lines = []
        for step in self._steps:
            attr_name = seen_widgets[(step.method, step.value)]
            if step.action == "click":
                simulate = step.args.get("simulate", False)
                button = step.args.get("button", "left")
                if simulate or button != "left":
                    action_lines.append(
                        f'        page.{attr_name}.click(simulate={simulate}, button="{button}")'
                    )
                else:
                    action_lines.append(f"        page.{attr_name}.click()")
            elif step.action == "press":
                button = step.args.get("button", "left")
                action_lines.append(f'        page.{attr_name}.press("{button}")')
            elif step.action == "release":
                button = step.args.get("button", "left")
                action_lines.append(f'        page.{attr_name}.release("{button}")')
            elif step.action == "set_enabled":
                enabled = step.args.get("enabled", True)
                action_lines.append(f"        page.{attr_name}.set_enabled({enabled})")

        descriptors = "\n".join(descriptor_lines)
        actions = "\n".join(action_lines)

        lines = [
            "# Generated by Matory Recorder",
            "from matory.page.page import Page, WidgetDescriptor",
            "from matory import Session",
            "",
            "",
            f"class {class_name}(Page):",
            descriptors,
            "",
            "",
            f"class Test{class_name}:",
            "    def test_recorded_flow(self, session):",
            f"        page = session.page({class_name})",
            actions,
        ]

        code = "\n".join(lines) + "\n"
        return code

    def generate_code(self, class_name: str, output_path: str) -> None:
        """Generate a pytest test file from the recorded steps.

        Widgets with the same (method, value) are deduplicated into a single
        Page Object descriptor.
        """
        code = self.render_code(class_name)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(code)
