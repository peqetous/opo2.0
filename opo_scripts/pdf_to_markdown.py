"""PDF (capa de texto) -> Markdown."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import fitz


QUESTION_NUMBER_RE = re.compile(r"^(\d{1,3})\.$")
INLINE_QUESTION_RE = re.compile(r"^(\d{1,3})\.\s+(.+)$")
OPTION_RE = re.compile(r"^([abc])[).]\s*(.*)$", re.IGNORECASE)
PAGE_NUMBER_RE = re.compile(r"^\d{1,2}$")


def _join_wrapped_lines(lines: list[str]) -> str:
    return " ".join(line.strip() for line in lines if line.strip())


def _is_page_footer(line: str) -> bool:
    return "Pág." in line or "PASE A LA PÁGINA" in line or "FIN DEL EXAMEN" in line


def _is_boilerplate_line(line: str) -> bool:
    return (
        "MADRID  -  ÁVILA" in line
        or line == "OPOSICIÓN INGRESO ESCALA EJECUTIVA"
        or line == "WWW.DE-POL.ES"
        or PAGE_NUMBER_RE.match(line) is not None
    )


def _split_extracted_lines(text: str) -> list[str]:
    lines: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            lines.append("")
            continue
        line = re.sub(r"(?<=[.:;?])\s+([abc])[).]\s+", r"\n\1) ", line, flags=re.IGNORECASE)
        line = re.sub(r"(?<!^)\s+([1-9][0-9]?|100)\.\s+", r"\n\1. ", line)
        lines.extend(part.strip() for part in line.splitlines())
    return lines


def _format_cover_or_instructions(text: str) -> str:
    lines = [line.strip() for line in text.splitlines()]
    out: list[str] = []
    i = 0

    while i < len(lines):
        line = lines[i]
        if not line:
            i += 1
            continue
        if line == "INSTRUCCIONES":
            out.append("## INSTRUCCIONES")
            i += 1
            continue
        if line in {"ώ", "ω"}:
            i += 1
            bullet_lines: list[str] = []
            while i < len(lines):
                next_line = lines[i].strip()
                if next_line in {"ώ", "ω"} or next_line.startswith("APELLIDOS"):
                    break
                if next_line:
                    bullet_lines.append(next_line)
                i += 1
            if bullet_lines:
                out.append(f"- {_join_wrapped_lines(bullet_lines)}")
            continue
        out.append(line)
        i += 1

    return "\n".join(out).strip()


def _flush_question(out: list[str], number: str, stem: list[str], options: list[tuple[str, list[str]]]) -> None:
    question = _join_wrapped_lines(stem)
    if question:
        out.append(f"**{number}.** {question}")
    else:
        out.append(f"**{number}.**")

    for letter, option_lines in options:
        option = _join_wrapped_lines(option_lines)
        out.append(f"{letter.lower()}) {option}")
    out.append("")


def format_page_text(text: str) -> str:
    """Format extracted exam-like text without inventing content."""
    if "INSTRUCCIONES" in text and not re.search(r"^\s*\d{1,3}\.", text, flags=re.MULTILINE):
        return _format_cover_or_instructions(text)
    if not re.search(r"^\s*\d{1,3}\.", text, flags=re.MULTILINE):
        cover_lines = [
            line.strip()
            for line in text.splitlines()
            if line.strip() and not _is_boilerplate_line(line.strip())
        ]
        return "\n".join(cover_lines).strip()

    lines = _split_extracted_lines(text)
    out: list[str] = []
    pending_stem_prefix: list[str] = []
    i = 0

    while i < len(lines):
        line = lines[i]
        if not line:
            i += 1
            continue

        if _is_page_footer(line):
            if pending_stem_prefix:
                out.append(_join_wrapped_lines(pending_stem_prefix))
                pending_stem_prefix = []
            out.append(f"*{line}*")
            out.append("")
            i += 1
            continue

        number_match = QUESTION_NUMBER_RE.match(line)
        inline_match = INLINE_QUESTION_RE.match(line)
        if number_match or inline_match:
            number = number_match.group(1) if number_match else inline_match.group(1)
            stem = [line for line in pending_stem_prefix if not _is_boilerplate_line(line)]
            pending_stem_prefix = []
            if inline_match:
                stem.append(inline_match.group(2))
            i += 1

            while i < len(lines):
                next_line = lines[i]
                if not next_line:
                    i += 1
                    continue
                if (
                    OPTION_RE.match(next_line)
                    or QUESTION_NUMBER_RE.match(next_line)
                    or INLINE_QUESTION_RE.match(next_line)
                    or _is_page_footer(next_line)
                ):
                    break
                stem.append(next_line)
                i += 1

            options: list[tuple[str, list[str]]] = []
            while i < len(lines):
                option_match = OPTION_RE.match(lines[i])
                if not option_match:
                    break
                letter = option_match.group(1)
                option_lines = [option_match.group(2)]
                i += 1
                while i < len(lines):
                    next_line = lines[i]
                    if not next_line:
                        i += 1
                        continue
                    if (
                        OPTION_RE.match(next_line)
                        or QUESTION_NUMBER_RE.match(next_line)
                        or INLINE_QUESTION_RE.match(next_line)
                        or _is_page_footer(next_line)
                    ):
                        break
                    # If the next line is followed by a standalone question number, it belongs to the
                    # next question stem; otherwise it is a wrapped option line.
                    if i + 1 < len(lines) and QUESTION_NUMBER_RE.match(lines[i + 1]):
                        break
                    option_lines.append(next_line)
                    i += 1
                options.append((letter, option_lines))

            _flush_question(out, number, stem, options)
            continue

        pending_stem_prefix.append(line)
        i += 1

    if pending_stem_prefix:
        out.append(_join_wrapped_lines(pending_stem_prefix))

    return "\n".join(line for line in out).strip()


def main() -> int:
    parser = argparse.ArgumentParser(description="Convierte texto incrustado en PDF a .md.")
    parser.add_argument(
        "pdf",
        type=Path,
        metavar="PATH",
        help="ruta al PDF",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        metavar="MD",
        help="salida .md (por defecto: mismo nombre que el PDF)",
    )
    parser.add_argument(
        "--no-split-pages",
        action="store_true",
        help="no insertar ## Página N entre páginas",
    )
    args = parser.parse_args()

    pdf_path = args.pdf.expanduser().resolve()
    if not pdf_path.is_file():
        print(f"error: no existe: {pdf_path}", file=sys.stderr)
        return 1

    out = args.output.expanduser().resolve() if args.output else pdf_path.with_suffix(".md")

    doc = fitz.open(pdf_path)
    chunks: list[str] = []
    try:
        split_pages = not args.no_split_pages
        for i in range(len(doc)):
            text = format_page_text(doc[i].get_text())
            if split_pages:
                if chunks:
                    chunks.append("")
                chunks.append(f"## Página {i + 1}")
                chunks.append("")
            if text:
                chunks.append(text)
            elif split_pages:
                chunks.append("*(sin texto extraíble en esta página)*")
    finally:
        doc.close()

    body = "\n".join(chunks).strip()
    md = body + "\n" if body else "\n"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(md, encoding="utf-8")
    print(f"Escrito {out}")
    return 0


__all__ = ["format_page_text", "main"]


if __name__ == "__main__":
    raise SystemExit(main())
