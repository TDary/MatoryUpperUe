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


# Maps server command names to human-friendly action names
_INTERACTION_CMPS: dict[str, str] = {
    "ClickWidget": "click",
    "PressWidget": "press",
    "ReleaseWidget": "release",
    "SetWidgetEnabled": "set_enabled",
}


class Recorder:
    """Wraps a Session to record widget interactions for code generation.

    Uses instance-level interception on the Session rather than
    monkey-patching the Widget class, so multiple Recorders can
    coexist safely.

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
        self._original_send_cmd = None

    @property
    def steps(self) -> list[Step]:
        """The list of recorded steps."""
        return self._steps

    def start(self) -> None:
        """Start recording widget interactions."""
        self._recording = True
        self._steps.clear()
        # Intercept at the Session level (instance-level, not class-level)
        self._original_send_cmd = self._session._send_cmd
        original = self._original_send_cmd
        recorder_self = self

        def patched_send_cmd(cmd: str, args: dict[str, Any] | None = None) -> dict:
            if cmd in _INTERACTION_CMPS and recorder_self._recording:
                action = _INTERACTION_CMPS[cmd]
                # Extract method/value from args (all interaction commands include them)
                method = args.get("method", "") if args else ""
                value = args.get("value", "") if args else ""
                step = Step(
                    action=action,
                    method=method,
                    value=value,
                    args=args or {},
                )
                recorder_self._steps.append(step)
            return original(cmd, args)

        self._session._send_cmd = patched_send_cmd  # type: ignore[assignment]

    def stop(self) -> None:
        """Stop recording and restore the original Session._send_cmd."""
        self._recording = False
        if self._original_send_cmd is not None:
            self._session._send_cmd = self._original_send_cmd  # type: ignore[assignment]
            self._original_send_cmd = None

    def generate_code(self, class_name: str, output_path: str) -> None:
        """Generate a pytest test file from the recorded steps.

        Widgets with the same (method, value) are deduplicated into a single
        Page Object descriptor.
        """
        # Deduplicate widgets
        seen_widgets: dict[tuple[str, str], str] = {}  # (method, value) -> attr_name
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

        # Build Page class
        descriptor_lines = []
        for (method, value), attr_name in seen_widgets.items():
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

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(code)
