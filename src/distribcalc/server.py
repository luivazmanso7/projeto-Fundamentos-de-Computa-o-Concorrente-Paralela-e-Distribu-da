"""TCP server exposing distributed prime computations to remote clients."""
from __future__ import annotations

import socket
import threading
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from time import perf_counter
from typing import Dict, Tuple

from . import tasks
from .protocol import Message, ProtocolError, encode_error, encode_response


@dataclass
class ServerConfig:
    host: str = "127.0.0.1"
    port: int = 9090
    backlog: int = 8
    worker_processes: int = 4


@dataclass
class ServerStats:
    total_requests: int = 0
    prime_checks: int = 0
    range_requests: int = 0
    range_counts: int = 0
    cumulative_duration: float = 0.0
    max_duration: float = 0.0
    active_clients: int = 0
    completed_clients: int = 0
    last_error: str | None = None

    def register_duration(self, duration: float) -> None:
        if duration > self.max_duration:
            self.max_duration = duration
        self.cumulative_duration += duration

    @property
    def average_duration(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return self.cumulative_duration / self.total_requests

    def snapshot(self) -> Dict[str, float | int | str | None]:
        return {
            "total_requests": self.total_requests,
            "prime_checks": self.prime_checks,
            "range_requests": self.range_requests,
            "range_counts": self.range_counts,
            "average_duration_sec": round(self.average_duration, 6),
            "max_duration_sec": round(self.max_duration, 6),
            "active_clients": self.active_clients,
            "completed_clients": self.completed_clients,
            "last_error": self.last_error,
        }


class TaskDispatcher:
    """Dispatches CPU-bound work to a pool of worker processes."""

    def __init__(self, worker_processes: int) -> None:
        self._executor = ProcessPoolExecutor(max_workers=worker_processes)
        self._stats = ServerStats()
        self._stats_lock = threading.Lock()

    def _update_stats(self, command: str, duration: float) -> None:
        with self._stats_lock:
            self._stats.total_requests += 1
            if command == "prime":
                self._stats.prime_checks += 1
            elif command == "range":
                self._stats.range_requests += 1
            elif command == "count":
                self._stats.range_counts += 1
            self._stats.register_duration(duration)

    def set_active_clients(self, value: int) -> None:
        with self._stats_lock:
            self._stats.active_clients = value

    def increment_completed_clients(self) -> None:
        with self._stats_lock:
            self._stats.completed_clients += 1

    def set_last_error(self, error: str) -> None:
        with self._stats_lock:
            self._stats.last_error = error

    def stats(self) -> Dict[str, float | int | str | None]:
        with self._stats_lock:
            return self._stats.snapshot()

    def execute_prime(self, number: int) -> Dict[str, int | bool | float]:
        started = perf_counter()
        result = self._executor.submit(tasks.is_prime, number).result()
        self._update_stats("prime", perf_counter() - started)
        return {"number": number, "is_prime": result}

    def execute_range(self, start: int, end: int) -> Dict[str, object]:
        started = perf_counter()
        primes = self._executor.submit(tasks.primes_in_range, start, end).result()
        duration = perf_counter() - started
        self._update_stats("range", duration)
        return {
            "start": start,
            "end": end,
            "count": len(primes),
            "primes": primes if len(primes) <= 200 else primes[:200],
            "truncated": len(primes) > 200,
            "duration_sec": round(duration, 6),
        }

    def execute_count(self, start: int, end: int) -> Dict[str, object]:
        started = perf_counter()
        count = self._executor.submit(tasks.count_primes, start, end).result()
        duration = perf_counter() - started
        self._update_stats("count", duration)
        return {
            "start": start,
            "end": end,
            "count": count,
            "duration_sec": round(duration, 6),
        }

    def shutdown(self) -> None:
        self._executor.shutdown(wait=True)


class DistributedPrimeServer:
    """Basic multi-threaded TCP server that offloads computation to processes."""

    def __init__(self, config: ServerConfig | None = None) -> None:
        self.config = config or ServerConfig()
        self._dispatcher = TaskDispatcher(worker_processes=self.config.worker_processes)
        self._shutdown_event = threading.Event()
        self._client_counter = 0
        self._client_counter_lock = threading.Lock()
        self._threads: list[threading.Thread] = []

    def _register_client(self, delta: int) -> int:
        with self._client_counter_lock:
            self._client_counter += delta
            current = self._client_counter
        self._dispatcher.set_active_clients(current)
        return current

    def serve_forever(self) -> None:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind((self.config.host, self.config.port))
            server_socket.listen(self.config.backlog)
            server_socket.settimeout(1.0)
            print(
                f"Server listening on {self.config.host}:{self.config.port} "
                f"with {self.config.worker_processes} workers"
            )
            try:
                while not self._shutdown_event.is_set():
                    try:
                        client_socket, address = server_socket.accept()
                    except socket.timeout:
                        continue
                    except OSError:
                        break
                    thread = threading.Thread(
                        target=self._handle_client,
                        args=(client_socket, address),
                        daemon=True,
                    )
                    thread.start()
                    self._threads.append(thread)
            finally:
                for thread in self._threads:
                    thread.join()
                self._dispatcher.shutdown()

    def shutdown(self) -> None:
        self._shutdown_event.set()

    def _handle_client(self, client_socket: socket.socket, address: Tuple[str, int]) -> None:
        client_id = self._register_client(+1)
        with client_socket:
            print(f"[client:{client_id}] connected from {address}")
            connection = client_socket.makefile("rwb")
            connection.write(encode_response({"message": "connected", "client_id": client_id}))
            connection.flush()
            while not self._shutdown_event.is_set():
                raw = connection.readline()
                if not raw:
                    break
                try:
                    message = Message.from_wire(raw.decode("utf-8").strip())
                    response_payload = self._dispatch_command(message)
                    connection.write(encode_response(response_payload))
                except (ProtocolError, ValueError) as exc:
                    self._dispatcher.set_last_error(str(exc))
                    connection.write(encode_error(str(exc)))
                except Exception as exc:  # unexpected error: keep serving other clients
                    self._dispatcher.set_last_error(repr(exc))
                    connection.write(encode_error("internal server error"))
                finally:
                    connection.flush()
        self._dispatcher.increment_completed_clients()
        current = self._register_client(-1)
        print(f"[client:{client_id}] disconnected, active={current}")

    def _dispatch_command(self, message: Message) -> Dict[str, object]:
        command = message.command
        data = message.data
        if command == "prime":
            number = _require_int(data, "number")
            return self._dispatcher.execute_prime(number)
        if command == "range":
            start = _require_int(data, "start")
            end = _require_int(data, "end")
            return self._dispatcher.execute_range(start, end)
        if command == "count":
            start = _require_int(data, "start")
            end = _require_int(data, "end")
            return self._dispatcher.execute_count(start, end)
        if command == "stats":
            return self._dispatcher.stats()
        raise ProtocolError(f"unknown command: {command}")


def _require_int(data: Dict[str, object], key: str) -> int:
    value = data.get(key)
    if not isinstance(value, int):
        raise ProtocolError(f"field '{key}' must be an integer")
    return value


def run_server() -> None:
    server = DistributedPrimeServer()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        server.shutdown()


if __name__ == "__main__":  # pragma: no cover
    run_server()
