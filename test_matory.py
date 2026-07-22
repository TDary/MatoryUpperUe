#!/usr/bin/env python3
"""Matory UE SDK 集成测试脚本。

用法: python test_matory.py [host] [port]
默认: localhost:2666
"""

from __future__ import annotations

import argparse
import json
import socket
import sys
import time
import traceback
from typing import Any


# ─── 协议常量 ──────────────────────────────────────────────────


class Cmd:
    """SDK 命令名注册表，与服务端 MatoComponent::RegisterCommands 一一对应。"""

    # 基础
    PING = "Ping"
    GET_SDK_VERSION = "GetSdkVersion"
    GET_ENGINE_VERSION = "GetEngineVersion"
    DISCONNECT = "Disconnect"

    # 查询
    GET_WIDGET_TREE = "GetWidgetTree"
    FIND_BUTTONS = "FindButtons"
    FIND_TEXT = "FindText"
    WIDGET_EXISTS = "WidgetExists"
    GET_WIDGET_DETAIL = "GetWidgetDetail"

    # 交互
    CLICK_WIDGET = "ClickWidget"
    PRESS_WIDGET = "PressWidget"
    RELEASE_WIDGET = "ReleaseWidget"
    SET_WIDGET_ENABLED = "SetWidgetEnabled"

    # 录制
    START_RECORD = "StartRecord"
    STOP_RECORD = "StopRecord"


class Method:
    """Widget 查找方式。"""

    ID = "id"
    NAME = "name"
    PATH = "path"


class Key:
    """协议 args 字段键名。"""

    METHOD = "method"
    VALUE = "value"
    ID = "id"
    FILTER = "filter"
    KEYWORD = "keyword"
    BUTTON = "button"
    SIMULATE = "simulate"
    ENABLED = "enabled"


class Button:
    """鼠标按键。"""

    LEFT = "left"
    MIDDLE = "middle"
    RIGHT = "right"


# ─── 客户端 ────────────────────────────────────────────────────


class MatoryClient:
    """Matory UE SDK 的 TCP 客户端封装。

    支持 with 语句自动关闭连接，内部维护 TCP 流缓冲解决拆包问题。
    """

    def __init__(self, host: str = "127.0.0.1", port: int = 2666) -> None:
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(5.0)
        self.sock.connect((host, port))
        self._req_id = 0
        self._recv_buf = b""  # TCP 流缓冲，跨调用保留未读完的数据

    def __enter__(self) -> MatoryClient:
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()

    def send_cmd(self, cmd: str, args: dict | None = None) -> dict:
        """发送命令并等待一条完整响应。"""
        if args is None:
            args = {}
        self._req_id += 1
        payload = json.dumps({"id": self._req_id, "cmd": cmd, "args": args}) + "\n"
        self.sock.sendall(payload.encode("utf-8"))

        # 从 TCP 流中提取以 \n 分隔的完整消息，保留多余数据
        while b"\n" not in self._recv_buf:
            chunk = self.sock.recv(4096)
            if not chunk:
                raise ConnectionError("连接已断开")
            self._recv_buf += chunk

        newline_pos = self._recv_buf.index(b"\n")
        line = self._recv_buf[:newline_pos]
        self._recv_buf = self._recv_buf[newline_pos + 1:]
        return json.loads(line.decode("utf-8"))

    def disconnect(self) -> dict:
        """发送 Disconnect 命令并关闭连接。"""
        resp = self.send_cmd(Cmd.DISCONNECT, {})
        self.close()
        return resp

    def close(self) -> None:
        """关闭底层 Socket。"""
        self.sock.close()


def parse_data_field(data: Any) -> Any:
    """统一解析 data 字段。

    服务端返回的 data 可能是 dict/list（已解析）或 str（需二次解析）。
    """
    if isinstance(data, (dict, list)):
        return data
    if isinstance(data, str):
        try:
            return json.loads(data)
        except (json.JSONDecodeError, ValueError):
            return data
    return data


# ─── 测试辅助 ──────────────────────────────────────────────────


class TestRunner:
    """轻量测试运行器，统计通过/失败数量并统一输出格式。"""

    def __init__(self) -> None:
        self.passed = 0
        self.failed = 0

    def section(self, title: str) -> None:
        print(f"\n=== {title} ===")

    def assert_ok(self, resp: dict, cmd: str) -> Any:
        """断言响应 code == 0，返回解析后的 data。"""
        code = resp.get("code", -999)
        if code == 0:
            self.passed += 1
        else:
            self.failed += 1
            print(f"  ✗ {cmd}: 期望 code=0, 实际 code={code}")
        return parse_data_field(resp.get("data"))

    def check(self, condition: bool, message: str) -> None:
        if condition:
            self.passed += 1
        else:
            self.failed += 1
            print(f"  ✗ {message}")

    def log(self, message: str) -> None:
        print(f"  {message}")

    def summary(self) -> bool:
        total = self.passed + self.failed
        print(f"\n=== 结果: {self.passed}/{total} 通过 ===")
        return self.failed == 0


def _get_first_button(client: MatoryClient) -> dict | None:
    """查找第一个 Button Widget，无按钮时返回 None。"""
    resp = client.send_cmd(Cmd.FIND_BUTTONS, {})
    if resp.get("code") != 0:
        return None
    buttons = parse_data_field(resp.get("data"))
    if not isinstance(buttons, list) or not buttons:
        return None
    return buttons[0]


# ─── 测试用例 ──────────────────────────────────────────────────


def test_ping(client: MatoryClient, runner: TestRunner) -> None:
    """心跳检测：验证连接与 SDK 可用性。"""
    runner.section("心跳检测")

    resp = client.send_cmd(Cmd.PING, {})
    data = runner.assert_ok(resp, Cmd.PING)
    runner.check(resp.get("msg") == "pong", f"{Cmd.PING}: 期望 msg=pong, 实际 msg={resp.get('msg')}")
    runner.log("连接正常，SDK 可用")


def test_basic_commands(client: MatoryClient, runner: TestRunner) -> None:
    """基础命令：SDK 版本与引擎版本。"""
    runner.section("基础命令")

    # GetSdkVersion
    resp = client.send_cmd(Cmd.GET_SDK_VERSION, {})
    data = runner.assert_ok(resp, Cmd.GET_SDK_VERSION)
    version = data if not isinstance(data, str) else data.strip('"')
    runner.check(version == "1.0.0", f"{Cmd.GET_SDK_VERSION}: 期望 1.0.0, 实际 {version}")
    runner.log(f"SDK 版本: {version}")

    # GetEngineVersion
    resp = client.send_cmd(Cmd.GET_ENGINE_VERSION, {})
    data = runner.assert_ok(resp, Cmd.GET_ENGINE_VERSION)
    engine_ver = data if not isinstance(data, str) else data.strip('"')
    runner.log(f"引擎版本: {engine_ver}")


def test_widget_query(client: MatoryClient, runner: TestRunner) -> None:
    """查询命令：Widget 树、按钮、文本。"""
    runner.section("查询命令")

    # GetWidgetTree
    resp = client.send_cmd(Cmd.GET_WIDGET_TREE, {})
    tree = runner.assert_ok(resp, Cmd.GET_WIDGET_TREE)
    tree_size = len(json.dumps(tree)) if tree else 0
    runner.log(f"Widget 树: {tree_size} chars")

    # FindButtons
    resp = client.send_cmd(Cmd.FIND_BUTTONS, {})
    buttons = runner.assert_ok(resp, Cmd.FIND_BUTTONS)
    if isinstance(buttons, list):
        runner.log(f"按钮数量: {len(buttons)}")
        for btn in buttons:
            runner.log(
                f"  id={btn.get('id')}, name={btn.get('name')}, "
                f"text={btn.get('text')}, path={btn.get('path')}"
            )
    else:
        runner.log(f"{Cmd.FIND_BUTTONS} 结果: {buttons}")

    # FindText
    resp = client.send_cmd(Cmd.FIND_TEXT, {Key.KEYWORD: ""})
    texts = runner.assert_ok(resp, Cmd.FIND_TEXT)
    if isinstance(texts, list):
        runner.log(f"文本 Widget 数量: {len(texts)}")
    else:
        runner.log(f"{Cmd.FIND_TEXT} 结果: code={resp.get('code')}")


def test_widget_interaction(client: MatoryClient, runner: TestRunner) -> None:
    """交互命令：存在性检查、详情、点击、启用/禁用。"""
    runner.section("交互命令")

    btn = _get_first_button(client)
    if not btn:
        runner.log("无可用按钮，跳过交互测试")
        return

    btn_id = btn.get("id")
    btn_name = btn.get("name", "")
    btn_path = btn.get("path", "")
    runner.log(f"目标按钮: id={btn_id}, name={btn_name}, path={btn_path}")

    # ── ID 寻址（推荐，O(1) 直查）──

    resp = client.send_cmd(Cmd.WIDGET_EXISTS, {Key.METHOD: Method.ID, Key.VALUE: str(btn_id)})
    data = runner.assert_ok(resp, f"{Cmd.WIDGET_EXISTS}({Method.ID})")
    runner.log(f"{Cmd.WIDGET_EXISTS}({Method.ID}={btn_id}): {data}")

    resp = client.send_cmd(Cmd.GET_WIDGET_DETAIL, {Key.ID: btn_id})
    detail = runner.assert_ok(resp, Cmd.GET_WIDGET_DETAIL)
    detail_type = detail.get("type", "N/A") if isinstance(detail, dict) else "N/A"
    runner.log(f"{Cmd.GET_WIDGET_DETAIL}({Method.ID}={btn_id}): type={detail_type}")

    resp = client.send_cmd(Cmd.CLICK_WIDGET, {
        Key.METHOD: Method.ID, Key.VALUE: str(btn_id),
        Key.SIMULATE: False, Key.BUTTON: Button.LEFT,
    })
    runner.assert_ok(resp, f"{Cmd.CLICK_WIDGET}(direct)")
    runner.log(f"{Cmd.CLICK_WIDGET}({Method.ID}={btn_id}, direct): code={resp['code']}, msg={resp['msg']}")

    resp = client.send_cmd(Cmd.CLICK_WIDGET, {
        Key.METHOD: Method.ID, Key.VALUE: str(btn_id),
        Key.SIMULATE: True, Key.BUTTON: Button.LEFT,
    })
    runner.assert_ok(resp, f"{Cmd.CLICK_WIDGET}(simulate)")
    runner.log(f"{Cmd.CLICK_WIDGET}({Method.ID}={btn_id}, simulate): code={resp['code']}, msg={resp['msg']}")

    resp = client.send_cmd(Cmd.SET_WIDGET_ENABLED, {
        Key.METHOD: Method.ID, Key.VALUE: str(btn_id), Key.ENABLED: True,
    })
    runner.assert_ok(resp, Cmd.SET_WIDGET_ENABLED)
    runner.log(f"{Cmd.SET_WIDGET_ENABLED}({Method.ID}={btn_id}, true): code={resp['code']}, msg={resp['msg']}")

    # ── Name 寻址 ──

    resp = client.send_cmd(Cmd.WIDGET_EXISTS, {Key.METHOD: Method.NAME, Key.VALUE: btn_name})
    runner.assert_ok(resp, f"{Cmd.WIDGET_EXISTS}({Method.NAME})")
    runner.log(f"{Cmd.WIDGET_EXISTS}({Method.NAME}={btn_name}): {parse_data_field(resp['data'])}")

    # ── Path 寻址（兜底，仅调试用）──

    resp = client.send_cmd(Cmd.WIDGET_EXISTS, {Key.METHOD: Method.PATH, Key.VALUE: btn_path})
    runner.assert_ok(resp, f"{Cmd.WIDGET_EXISTS}({Method.PATH})")
    runner.log(f"{Cmd.WIDGET_EXISTS}({Method.PATH}={btn_path}): {parse_data_field(resp['data'])}  [兜底方式]")


def test_press_release(client: MatoryClient, runner: TestRunner) -> None:
    """按下/抬起分离测试，支持拖拽等复杂操作。"""
    runner.section("按下/抬起")

    btn = _get_first_button(client)
    if not btn:
        runner.log("无可用按钮，跳过 Press/Release 测试")
        return

    btn_id = btn.get("id")
    runner.log(f"目标按钮: id={btn_id}")

    resp = client.send_cmd(Cmd.PRESS_WIDGET, {
        Key.METHOD: Method.ID, Key.VALUE: str(btn_id), Key.BUTTON: Button.LEFT,
    })
    runner.assert_ok(resp, Cmd.PRESS_WIDGET)
    runner.log(f"{Cmd.PRESS_WIDGET}({Method.ID}={btn_id}): code={resp['code']}, msg={resp['msg']}")

    time.sleep(0.1)

    resp = client.send_cmd(Cmd.RELEASE_WIDGET, {
        Key.METHOD: Method.ID, Key.VALUE: str(btn_id), Key.BUTTON: Button.LEFT,
    })
    runner.assert_ok(resp, Cmd.RELEASE_WIDGET)
    runner.log(f"{Cmd.RELEASE_WIDGET}({Method.ID}={btn_id}): code={resp['code']}, msg={resp['msg']}")


def test_ui_recording(client: MatoryClient, runner: TestRunner) -> None:
    """UI 录制命令。"""
    runner.section("UI 录制")

    resp = client.send_cmd(Cmd.START_RECORD, {})
    runner.assert_ok(resp, Cmd.START_RECORD)
    runner.log(f"{Cmd.START_RECORD}: {resp['msg']}")

    runner.log("录制已启动 — 手动点击 UI 元素以触发事件")
    time.sleep(3)

    resp = client.send_cmd(Cmd.STOP_RECORD, {})
    runner.assert_ok(resp, Cmd.STOP_RECORD)
    runner.log(f"{Cmd.STOP_RECORD}: {resp['msg']}")


# ─── 入口 ──────────────────────────────────────────────────────


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Matory UE SDK 集成测试")
    parser.add_argument("host", nargs="?", default="127.0.0.1",
                        help="服务端地址 (默认: 127.0.0.1)")
    parser.add_argument("port", nargs="?", type=int, default=2666,
                        help="服务端端口 (默认: 2666)")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    print(f"连接 Matory UE SDK: {args.host}:{args.port} ...")
    try:
        with MatoryClient(args.host, args.port) as client:
            print("已连接!")
            runner = TestRunner()

            try:
                test_ping(client, runner)
                test_basic_commands(client, runner)
                test_widget_query(client, runner)
                test_widget_interaction(client, runner)
                test_press_release(client, runner)
                test_ui_recording(client, runner)
            except Exception:
                traceback.print_exc()

            if not runner.summary():
                sys.exit(1)
    except ConnectionError as e:
        print(f"连接失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
