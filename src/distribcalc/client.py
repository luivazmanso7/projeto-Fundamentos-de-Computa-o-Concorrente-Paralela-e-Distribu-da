"""Command-line client for the distributed prime computation service."""
from __future__ import annotations

import json
import socket
import threading
from dataclasses import dataclass
from typing import Optional

from .protocol import Message


@dataclass
class ClientConfig:
    host: str = "127.0.0.1"
    port: int = 9090


class ClientListener(threading.Thread):
    """Background thread responsible for printing server responses."""

    def __init__(self, connection: socket.socket) -> None:
        super().__init__(daemon=True)
        self.connection = connection
        self._stop_event = threading.Event()

    def run(self) -> None:  # pragma: no cover - interactive component
        with self.connection.makefile("rb") as stream:
            while not self._stop_event.is_set():
                chunk = stream.readline()
                if not chunk:
                    print("\n[server closed the connection]")
                    break
                try:
                    message = json.loads(chunk.decode("utf-8"))
                except json.JSONDecodeError:
                    print(f"\n[malformed response]: {chunk!r}")
                    continue
                status = message.get("status")
                payload = message.get("payload")
                print(f"\n[{status}] {json.dumps(payload, ensure_ascii=False, indent=2)}")
                print("distribcalc> ", end="", flush=True)

    def stop(self) -> None:
        self._stop_event.set()


def parse_user_input(raw: str) -> Optional[Message]:
    parts = raw.strip().split()
    if not parts:
        return None
    command = parts[0].lower()
    if command in {"quit", "exit"}:
        raise KeyboardInterrupt
    if command == "prime" and len(parts) == 2:
        return Message(command="prime", data={"number": int(parts[1])})
    if command == "range" and len(parts) == 3:
        return Message(
            command="range",
            data={"start": int(parts[1]), "end": int(parts[2])},
        )
    if command == "count" and len(parts) == 3:
        return Message(
            command="count",
            data={"start": int(parts[1]), "end": int(parts[2])},
        )
    if command == "stats" and len(parts) == 1:
        return Message(command="stats", data={})
    raise ValueError("Comando inválido. Use prime <n>, range <a> <b>, count <a> <b> ou stats.")


def run_client(config: ClientConfig | None = None) -> None:
    config = config or ClientConfig()
    address = (config.host, config.port)
    try:
        with socket.create_connection(address) as connection:
            listener = ClientListener(connection)
            listener.start()
            print("Conectado ao servidor. Comandos disponíveis:")
            print("  prime <n>    → verifica se n é primo")
            print("  range <a> <b> → lista primos no intervalo")
            print("  count <a> <b> → conta primos no intervalo")
            print("  stats         → estatísticas do servidor")
            print("  exit          → encerra o cliente")
            while True:
                try:
                    raw = input("distribcalc> ")
                    message = parse_user_input(raw)
                    if message is None:
                        continue
                    connection.sendall(message.to_wire())
                except ValueError as exc:
                    print(f"[erro] {exc}")
                except KeyboardInterrupt:
                    print("\nEncerrando cliente...")
                    break
    except ConnectionRefusedError:
        print(f"Não foi possível conectar a {address[0]}:{address[1]}")


if __name__ == "__main__":  # pragma: no cover
    run_client()
