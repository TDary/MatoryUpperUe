"""Protocol constants and message encode/decode for Matory UE SDK."""

from __future__ import annotations

import json
from typing import Any


class Cmd:
    """SDK command names — one-to-one with server MatoComponent::RegisterCommands."""

    # Basic
    GET_SDK_VERSION = "GetSdkVersion"
    GET_ENGINE_VERSION = "GetEngineVersion"
    DISCONNECT = "Disconnect"

    # Query
    GET_WIDGET_TREE = "GetWidgetTree"
    FIND_BUTTONS = "FindButtons"
    FIND_TEXT = "FindText"
    WIDGET_EXISTS = "WidgetExists"
    GET_WIDGET_DETAIL = "GetWidgetDetail"

    # Interaction
    CLICK_WIDGET = "ClickWidget"
    PRESS_WIDGET = "PressWidget"
    RELEASE_WIDGET = "ReleaseWidget"
    SET_WIDGET_ENABLED = "SetWidgetEnabled"

    # Recording
    START_RECORD = "StartRecord"
    STOP_RECORD = "StopRecord"


class Method:
    """Widget lookup method."""

    ID = "id"
    NAME = "name"
    PATH = "path"


class Key:
    """Protocol args field key names."""

    METHOD = "method"
    VALUE = "value"
    ID = "id"
    FILTER = "filter"
    KEYWORD = "keyword"
    BUTTON = "button"
    SIMULATE = "simulate"
    ENABLED = "enabled"


class Button:
    """Mouse button identifiers."""

    LEFT = "left"
    MIDDLE = "middle"
    RIGHT = "right"


def encode_request(req_id: int, cmd: str, args: dict[str, Any]) -> bytes:
    """Encode a request dict to JSON bytes with a trailing newline."""
    payload = json.dumps({"id": req_id, "cmd": cmd, "args": args}) + "\n"
    return payload.encode("utf-8")


def _parse_data_field(data: Any) -> Any:
    """Normalize the data field from a server response.

    The server may return data as dict/list (already parsed) or as a
    JSON string that needs a second parse.
    """
    if isinstance(data, (dict, list)):
        return data
    if isinstance(data, str):
        try:
            return json.loads(data)
        except (json.JSONDecodeError, ValueError):
            return data
    return data


def decode_response(line: str) -> dict[str, Any]:
    """Decode a newline-delimited JSON response line.

    The ``data`` field is normalized via ``_parse_data_field``.
    """
    resp = json.loads(line)
    if "data" in resp:
        resp["data"] = _parse_data_field(resp["data"])
    return resp
