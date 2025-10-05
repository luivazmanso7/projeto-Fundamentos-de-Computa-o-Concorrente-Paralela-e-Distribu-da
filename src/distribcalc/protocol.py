"""Utilities for encoding and decoding the application protocol."""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict


class ProtocolError(Exception):
    """Raised when the server receives an invalid message."""


@dataclass
class Message:
    """Convenience container for protocol messages."""

    command: str
    data: Dict[str, Any]

    def to_wire(self) -> bytes:
        payload = {"command": self.command, "data": self.data}
        return json.dumps(payload).encode("utf-8") + b"\n"

    @staticmethod
    def from_wire(raw: str) -> "Message":
        try:
            loaded = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ProtocolError("payload is not valid JSON") from exc
        if not isinstance(loaded, dict):
            raise ProtocolError("payload must be a JSON object")
        command = loaded.get("command")
        if not isinstance(command, str):
            raise ProtocolError("command field must be a string")
        data = loaded.get("data")
        if data is None:
            data = {}
        if not isinstance(data, dict):
            raise ProtocolError("data field must be a JSON object")
        return Message(command=command.lower(), data=data)


def encode_response(payload: Dict[str, Any], *, status: str = "ok") -> bytes:
    message = {"status": status, "payload": payload}
    return json.dumps(message).encode("utf-8") + b"\n"


def encode_error(message: str) -> bytes:
    return encode_response({"error": message}, status="error")
