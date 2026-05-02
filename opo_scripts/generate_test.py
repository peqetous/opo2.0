"""Genera tests HTML interactivos a partir de preguntas en JSON."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from html import escape
from pathlib import Path
from typing import Any


VALID_SCOPE_TYPES = {"general", "temas", "leyes"}
VALID_LETTERS = {"a", "b", "c"}


class TestGenerationError(ValueError):
    """Error de validación del test de entrada."""


@dataclass(frozen=True)
class Question:
    enunciado: str
    opciones: dict[str, str]
    correcta: str
    explicacion: str
    fuente: str | None = None


def _require_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise TestGenerationError(f"`{field}` debe ser una cadena no vacía.")
    return value.strip()


def _normalize_scope_id(value: Any, scope_type: str) -> str:
    if scope_type == "general":
        return ""
    if isinstance(value, list):
        parts = [str(part).strip() for part in value if str(part).strip()]
        if not parts:
            raise TestGenerationError("`scope_id` no puede estar vacío.")
        return "-".join(parts)
    return _require_string(value, "scope_id")


def _normalize_options(raw: Any, index: int) -> dict[str, str]:
    if isinstance(raw, list):
        if len(raw) != 3:
            raise TestGenerationError(f"La pregunta {index} debe tener exactamente 3 opciones.")
        return {letter: _require_string(raw[i], f"preguntas[{index}].opciones[{letter}]") for i, letter in enumerate(("a", "b", "c"))}

    if isinstance(raw, dict):
        missing = VALID_LETTERS - set(raw)
        extra = set(raw) - VALID_LETTERS
        if missing or extra:
            raise TestGenerationError(
                f"La pregunta {index} debe tener opciones a, b y c; faltan {sorted(missing)} y sobran {sorted(extra)}."
            )
        return {letter: _require_string(raw[letter], f"preguntas[{index}].opciones.{letter}") for letter in ("a", "b", "c")}

    raise TestGenerationError(f"`preguntas[{index}].opciones` debe ser lista de 3 textos u objeto con a/b/c.")


def _parse_question(raw: Any, index: int) -> Question:
    if not isinstance(raw, dict):
        raise TestGenerationError(f"`preguntas[{index}]` debe ser un objeto.")

    correcta = _require_string(raw.get("correcta"), f"preguntas[{index}].correcta").lower()
    if correcta not in VALID_LETTERS:
        raise TestGenerationError(f"`preguntas[{index}].correcta` debe ser a, b o c.")

    fuente = raw.get("fuente")
    if fuente is not None and not isinstance(fuente, str):
        raise TestGenerationError(f"`preguntas[{index}].fuente` debe ser texto si se informa.")

    return Question(
        enunciado=_require_string(raw.get("enunciado"), f"preguntas[{index}].enunciado"),
        opciones=_normalize_options(raw.get("opciones"), index),
        correcta=correcta,
        explicacion=_require_string(raw.get("explicacion"), f"preguntas[{index}].explicacion"),
        fuente=fuente.strip() if isinstance(fuente, str) and fuente.strip() else None,
    )


def load_payload(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise TestGenerationError(f"JSON inválido en {path}: {exc}") from exc

    if not isinstance(data, dict):
        raise TestGenerationError("El JSON raíz debe ser un objeto.")
    return data


def parse_payload(data: dict[str, Any]) -> tuple[str, str, str, str, list[Question]]:
    title = _require_string(data.get("title", "Test"), "title")
    scope_type = _require_string(data.get("scope_type"), "scope_type").lower()
    if scope_type not in VALID_SCOPE_TYPES:
        raise TestGenerationError(f"`scope_type` debe ser uno de {sorted(VALID_SCOPE_TYPES)}.")

    scope_id = _normalize_scope_id(data.get("scope_id", ""), scope_type)
    date = _require_string(data.get("date") or datetime.now().strftime("%d%m%Y"), "date")
    if not re.fullmatch(r"\d{8}", date):
        raise TestGenerationError("`date` debe usar formato DDMMAAAA.")

    raw_questions = data.get("preguntas")
    if not isinstance(raw_questions, list) or not raw_questions:
        raise TestGenerationError("`preguntas` debe ser una lista no vacía.")

    questions = [_parse_question(raw, i) for i, raw in enumerate(raw_questions, start=1)]
    return title, scope_type, scope_id, date, questions


def output_name(scope_type: str, scope_id: str, date: str) -> str:
    if scope_type == "general":
        return f"test_general_{date}.html"
    return f"test_{scope_type}_{scope_id}_{date}.html"


def available_output_path(output_dir: Path, filename: str) -> Path:
    output_path = output_dir / filename
    if not output_path.exists():
        return output_path

    stem = output_path.stem
    suffix = output_path.suffix
    version = 1
    while True:
        candidate = output_dir / f"{stem}_{version:02d}{suffix}"
        if not candidate.exists():
            return candidate
        version += 1


def _extract_between(text: str, start: str, end: str, label: str) -> str:
    pattern = re.escape(start) + r"(.*?)" + re.escape(end)
    match = re.search(pattern, text, flags=re.DOTALL)
    if not match:
        raise TestGenerationError(f"No se pudo extraer {label} de la plantilla.")
    return match.group(1)


def load_template_parts(template_path: Path) -> tuple[str, str]:
    template = template_path.read_text(encoding="utf-8")
    style = _extract_between(template, "<style>", "</style>", "el bloque CSS")

    script_match = re.search(r"    const IDS = Object\.keys\(CORRECTAS\);.*?  </script>", template, flags=re.DOTALL)
    if not script_match:
        raise TestGenerationError("No se pudo extraer el script base de la plantilla.")
    script_tail = script_match.group(0).removesuffix("  </script>")
    return style, script_tail


def render_questions(questions: list[Question]) -> str:
    blocks: list[str] = []
    for i, question in enumerate(questions, start=1):
        source = f"<!-- Fuente: {escape(question.fuente)} -->" if question.fuente else "<!-- Fuente: indicada en EXPLICACIONES -->"
        blocks.append(
            f"""        {source}
        <fieldset data-q="q{i}">
          <legend class="visually-hidden">Pregunta {i}</legend>
          <div class="enunciado" id="enun-q{i}"><strong>{i}.</strong> {escape(question.enunciado)}</div>
          <div class="options" role="radiogroup" aria-labelledby="enun-q{i}">
            <label><input type="radio" name="q{i}" value="a" /> a) {escape(question.opciones["a"])}</label>
            <label><input type="radio" name="q{i}" value="b" /> b) {escape(question.opciones["b"])}</label>
            <label><input type="radio" name="q{i}" value="c" /> c) {escape(question.opciones["c"])}</label>
            <label class="opt-skip"><input type="radio" name="q{i}" value="_skip" checked /> Sin responder</label>
          </div>
        </fieldset>"""
        )
    return "\n".join(blocks)


def render_html(title: str, questions: list[Question], template_path: Path, exam_name: str) -> str:
    style, script_tail = load_template_parts(template_path)
    correctas = {f"q{i}": question.correcta for i, question in enumerate(questions, start=1)}
    explicaciones = {f"q{i}": question.explicacion for i, question in enumerate(questions, start=1)}
    question_count = len(questions)

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <meta name="color-scheme" content="light" />
  <title>{escape(title)}</title>
  <style>{style}  </style>
</head>
<body>
  <header class="topbar">
    <h1 class="topbar-title">{escape(title)}</h1>
    <div id="timer-block" class="timer-block inactivo" aria-live="polite">
      <span class="timer-caption">Transcurrido</span>
      <span id="timer" class="timer-value">0:00</span>
    </div>
  </header>

  <main>
    <section id="panel-inicio" class="sheet inicio">
      <p class="lead">
        Pulsa <strong>Empezar</strong> para iniciar el cronómetro y ver las {question_count} preguntas.
        Puedes pulsar <strong>Corregir</strong> cuando quieras; las que dejes en «Sin responder» no suman ni restan.
      </p>
      <p class="hint">
        Puntuación (solo sobre las contestadas, excluido «Sin responder»): cada 2 incorrectas restan 1 acierto (la nota puede ser negativa).
      </p>
      <button type="button" class="btn btn-primary" id="btn-empezar">Empezar</button>
    </section>

    <section id="panel-examen" hidden>
      <form id="form-examen">
{render_questions(questions)}
        <div class="acciones">
          <button type="submit" class="btn btn-primary" id="btn-corregir" disabled>Corregir</button>
          <p class="hint" id="hint-completo">
            Las preguntas no son obligatorias. «Sin responder» queda fuera de la nota.
          </p>
        </div>
      </form>
    </section>

    <section id="panel-resultados" class="sheet result-block" hidden>
      <h2>Resultado</h2>
      <p class="puntos" id="out-puntos"></p>
      <p class="detalle" id="out-detalle"></p>
      <p class="result-muted" id="out-guardado" hidden></p>
      <div class="bloque-repaso" id="bloque-fallidas">
        <h3>Fallidas</h3>
        <p class="result-muted" id="out-msg-fallidas" hidden></p>
        <ul class="err-list" id="out-errores"></ul>
      </div>
      <div class="bloque-repaso" id="bloque-omitidas" hidden>
        <h3>Sin responder</h3>
        <ul class="err-list omit-list" id="out-omitidas"></ul>
      </div>
      <p class="sin-errores" id="out-sin-errores" hidden></p>
    </section>
  </main>

  <script>
    const SKIP = "_skip";
    const EXAMEN_ID = {json.dumps(exam_name, ensure_ascii=False)};
    const RESULTADOS_ENDPOINT = "http://127.0.0.1:8765/resultados-test";
    const CORRECTAS = {json.dumps(correctas, ensure_ascii=False, indent=6)};
    const EXPLICACIONES = {json.dumps(explicaciones, ensure_ascii=False, indent=6)};
{script_tail}
  </script>
</body>
</html>
"""


def validate_rendered(html: str, question_count: int) -> None:
    checks = {
        "fieldset": html.count("<fieldset data-q="),
        "opción Sin responder": html.count('value="_skip" checked'),
        "legend": html.count('<legend class="visually-hidden">Pregunta '),
    }
    for label, count in checks.items():
        if count != question_count:
            raise TestGenerationError(f"Validación HTML fallida: {label}={count}, esperado={question_count}.")

    if "const CORRECTAS" not in html or "const EXPLICACIONES" not in html:
        raise TestGenerationError("Validación HTML fallida: faltan CORRECTAS o EXPLICACIONES.")


def generate(input_path: Path, output_dir: Path, template_path: Path) -> Path:
    title, scope_type, scope_id, date, questions = parse_payload(load_payload(input_path))

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = available_output_path(output_dir, output_name(scope_type, scope_id, date))
    html = render_html(title, questions, template_path, output_path.name)
    validate_rendered(html, len(questions))
    output_path.write_text(html, encoding="utf-8")
    return output_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Genera un test HTML interactivo desde un JSON de preguntas.")
    parser.add_argument("input", type=Path, help="JSON con metadatos y preguntas")
    parser.add_argument("-o", "--output-dir", type=Path, default=Path("test_generados"), help="directorio de salida")
    parser.add_argument(
        "--template",
        type=Path,
        default=Path("utilidades/examen-prueba.html"),
        help="plantilla HTML base",
    )
    args = parser.parse_args()

    try:
        output_path = generate(args.input, args.output_dir, args.template)
    except TestGenerationError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
