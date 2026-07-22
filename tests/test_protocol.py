"""Tests for protocol constants and encode/decode."""

import json

from matory.client.protocol import (
    Cmd, Method, Key, Button,
    encode_request, decode_response,
)


# -- Constants --


def test_cmd_constants():
    assert Cmd.GET_SDK_VERSION == "GetSdkVersion"
    assert Cmd.GET_ENGINE_VERSION == "GetEngineVersion"
    assert Cmd.DISCONNECT == "Disconnect"
    assert Cmd.GET_WIDGET_TREE == "GetWidgetTree"
    assert Cmd.FIND_BUTTONS == "FindButtons"
    assert Cmd.FIND_TEXT == "FindText"
    assert Cmd.WIDGET_EXISTS == "WidgetExists"
    assert Cmd.GET_WIDGET_DETAIL == "GetWidgetDetail"
    assert Cmd.CLICK_WIDGET == "ClickWidget"
    assert Cmd.PRESS_WIDGET == "PressWidget"
    assert Cmd.RELEASE_WIDGET == "ReleaseWidget"
    assert Cmd.SET_WIDGET_ENABLED == "SetWidgetEnabled"
    assert Cmd.START_RECORD == "StartRecord"
    assert Cmd.STOP_RECORD == "StopRecord"


def test_method_constants():
    assert Method.ID == "id"
    assert Method.NAME == "name"
    assert Method.PATH == "path"


def test_key_constants():
    assert Key.METHOD == "method"
    assert Key.VALUE == "value"
    assert Key.ID == "id"
    assert Key.FILTER == "filter"
    assert Key.KEYWORD == "keyword"
    assert Key.BUTTON == "button"
    assert Key.SIMULATE == "simulate"
    assert Key.ENABLED == "enabled"


def test_button_constants():
    assert Button.LEFT == "left"
    assert Button.MIDDLE == "middle"
    assert Button.RIGHT == "right"


# -- Encode --


def test_encode_request_basic():
    result = encode_request(1, "GetSdkVersion", {})
    parsed = json.loads(result.decode("utf-8"))
    assert parsed == {"id": 1, "cmd": "GetSdkVersion", "args": {}}


def test_encode_request_with_args():
    result = encode_request(5, "ClickWidget", {"method": "id", "value": "42"})
    parsed = json.loads(result.decode("utf-8"))
    assert parsed == {"id": 5, "cmd": "ClickWidget", "args": {"method": "id", "value": "42"}}


def test_encode_request_ends_with_newline():
    result = encode_request(1, "GetSdkVersion", {})
    assert result.endswith(b"\n")


# -- Decode --


def test_decode_response_dict_data():
    line = json.dumps({"id": 1, "code": 0, "msg": "ok", "data": {"type": "Button"}})
    resp = decode_response(line)
    assert resp["code"] == 0
    assert resp["data"] == {"type": "Button"}


def test_decode_response_string_data_parsed():
    """When data is a JSON string, decode_response should parse it."""
    inner = json.dumps({"type": "Button", "name": "LoginBtn"})
    line = json.dumps({"id": 1, "code": 0, "msg": "ok", "data": inner})
    resp = decode_response(line)
    assert resp["data"] == {"type": "Button", "name": "LoginBtn"}


def test_decode_response_string_data_not_json():
    """When data is a plain string that isn't JSON, keep it as-is."""
    line = json.dumps({"id": 1, "code": 0, "msg": "ok", "data": "1.0.0"})
    resp = decode_response(line)
    assert resp["data"] == "1.0.0"


def test_decode_response_list_data():
    line = json.dumps({"id": 1, "code": 0, "msg": "ok", "data": [1, 2, 3]})
    resp = decode_response(line)
    assert resp["data"] == [1, 2, 3]


def test_decode_response_none_data():
    line = json.dumps({"id": 1, "code": 1, "msg": "error", "data": None})
    resp = decode_response(line)
    assert resp["data"] is None


def test_decode_response_malformed_json_raises_matory_error():
    """Malformed JSON from server should raise MatoryError, not json.JSONDecodeError."""
    import pytest
    from matory.errors import MatoryError
    with pytest.raises(MatoryError, match="Malformed response"):
        decode_response("not valid json{{{")
