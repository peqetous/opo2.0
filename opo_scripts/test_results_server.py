"""Servidor local para registrar intentos de tests en CSV."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any


DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765
DEFAULT_CSV_PATH = Path("utilidades/resultados_test.csv")
CSV_FIELDS = [
    "fecha_intento",
    "examen",
    "preguntas_respondidas",
    "preguntas_sin_responder",
    "aciertos",
    "fallos",
    "resultado",
]


class ResultsRequestHandler(BaseHTTPRequestHandler):
    server: ResultsServer

    def _send_json(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Private-Network", "true")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Private-Network", "true")
        self.end_headers()

    def do_POST(self) -> None:
        if self.path != "/resultados-test":
            self._send_json(404, {"ok": False, "error": "Endpoint no encontrado."})
            return

        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            raw_body = self.rfile.read(content_length)
            payload = json.loads(raw_body.decode("utf-8"))
            row = build_csv_row(payload)
            append_csv_row(self.server.csv_path, row)
        except (ValueError, json.JSONDecodeError) as exc:
            self._send_json(400, {"ok": False, "error": str(exc)})
            return
        except OSError as exc:
            self._send_json(500, {"ok": False, "error": f"No se pudo escribir el CSV: {exc}"})
            return

        self._send_json(200, {"ok": True})

    def log_message(self, format: str, *args: Any) -> None:
        print(f"{self.address_string()} - {format % args}", file=sys.stderr)


class ResultsServer(ThreadingHTTPServer):
    def __init__(self, server_address: tuple[str, int], csv_path: Path) -> None:
        super().__init__(server_address, ResultsRequestHandler)
        self.csv_path = csv_path


def _required_int(payload: dict[str, Any], field: str) -> int:
    value = payload.get(field)
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"`{field}` debe ser un número entero.")
    if value < 0:
        raise ValueError(f"`{field}` no puede ser negativo.")
    return value


def _required_number(payload: dict[str, Any], field: str) -> int | float:
    value = payload.get(field)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"`{field}` debe ser numérico.")
    return value


def build_csv_row(payload: Any) -> dict[str, str | int | float]:
    if not isinstance(payload, dict):
        raise ValueError("El cuerpo de la petición debe ser un objeto JSON.")

    examen = payload.get("examen")
    if not isinstance(examen, str) or not examen.strip():
        raise ValueError("`examen` debe ser texto no vacío.")

    return {
        "fecha_intento": datetime.now().isoformat(timespec="seconds"),
        "examen": examen.strip(),
        "preguntas_respondidas": _required_int(payload, "preguntas_respondidas"),
        "preguntas_sin_responder": _required_int(payload, "preguntas_sin_responder"),
        "aciertos": _required_int(payload, "aciertos"),
        "fallos": _required_int(payload, "fallos"),
        "resultado": _required_number(payload, "resultado"),
    }


def append_csv_row(csv_path: Path, row: dict[str, str | int | float]) -> None:
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    needs_header = not csv_path.exists() or csv_path.stat().st_size == 0
    with csv_path.open("a", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=CSV_FIELDS)
        if needs_header:
            writer.writeheader()
        writer.writerow(row)


def main() -> int:
    parser = argparse.ArgumentParser(description="Registra resultados de tests en utilidades/resultados_test.csv.")
    parser.add_argument("--host", default=DEFAULT_HOST, help="host de escucha")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="puerto de escucha")
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV_PATH, help="ruta del CSV de resultados")
    args = parser.parse_args()

    server = ResultsServer((args.host, args.port), args.csv)
    print(f"Registrando resultados en {args.csv}")
    print(f"Servidor disponible en http://{args.host}:{args.port}/resultados-test")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor detenido.")
    finally:
        server.server_close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
