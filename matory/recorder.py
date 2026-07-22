"""Recorder — intercepts Widget operations and generates pytest test code."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from matory.elements.widget import Widget
from matory.session import Session


@dataclass
class Step:
    """A single recorded widget action."""

    action: str
    method: str
    value: str
    args: dict[str, Any] = field(default_factory=dict)


class Recorder:
    """Wraps a Session to record widget interactions for code generation.

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
        # Monkey-patch Widget._send_cmd to intercept
        self._original_send_cmd = Widget._send_cmd
        original = self._original_send_cmd

        recorder_self = self

        def patched_send_cmd(widget_self: Widget, cmd: str, args: dict[str, Any] | None = None) -> dict:
            # Record interaction actions
            interaction_cmds = {
                "ClickWidget": "click",
                "PressWidget": "press",
                "ReleaseWidget": "release",
                "SetWidgetEnabled": "set_enabled",
            }
            if cmd in interaction_cmds and recorder_self._recording:
                action = interaction_cmds[cmd]
                step = Step(
                    action=action,
                    method=widget_self._method,
                    value=widget_self._value,
                    args=args or {},
                )
                recorder_self._steps.append(step)
            # Still call the original to actually perform the action
            return original(widget_self, cmd, args)

        Widget._send_cmd = patched_send_cmd

    def stop(self) -> None:
        """Stop recording and restore the original Widget._send_cmd."""
        self._recording = False
        if self._original_send_cmd is not None:
            Widget._send_cmd = self._original_send_cmd
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
                # Generate a Python-safe attribute name preserving original casing
                safe_name = step.value.replace(" ", "_").replace("/", "_")
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
            "from matory.page.page import *",
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
