#!/usr/bin/env bash
set -euo pipefail

LIST_FILE="${1:-example.txt}"
OUT_DIR="${2:-log_leyes}"
INCLUDE_PATCHES="${INCLUDE_PATCHES:-0}"

if [[ ! -f "$LIST_FILE" ]]; then
  echo "No existe el archivo de lista: $LIST_FILE" >&2
  exit 1
fi

mkdir -p "$OUT_DIR"

if [[ -z "${GITHUB_TOKEN:-}" && -n "${GH_TOKEN:-}" ]]; then
  export GITHUB_TOKEN="$GH_TOKEN"
fi

if [[ -z "${GITHUB_TOKEN:-}" ]] && command -v gh >/dev/null 2>&1; then
  GITHUB_TOKEN="$(gh auth token 2>/dev/null || true)"
  export GITHUB_TOKEN
fi

python3 - "$LIST_FILE" "$OUT_DIR" "$INCLUDE_PATCHES" <<'PY'
import json
import os
import re
import sys
import time
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


LIST_FILE = Path(sys.argv[1])
OUT_DIR = Path(sys.argv[2])
INCLUDE_PATCHES = sys.argv[3] == "1"
TOKEN = os.environ.get("GITHUB_TOKEN")


def github_request(url):
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "opo2-legal-history-export",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"

    request = Request(url, headers=headers)
    try:
        with urlopen(request) as response:
            return json.loads(response.read().decode("utf-8")), response.headers
    except HTTPError as error:
        body = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GitHub API error {error.code} for {url}: {body}") from error


def parse_url(url):
    patterns = [
        r"^https://github\.com/([^/]+)/([^/]+)/blob/([^/]+)/(.+)$",
        r"^https://raw\.githubusercontent\.com/([^/]+)/([^/]+)/([^/]+)/(.+)$",
    ]
    for pattern in patterns:
        match = re.match(pattern, url)
        if match:
            return match.groups()
    return None


def read_source_urls():
    for raw_line in LIST_FILE.read_text(encoding="utf-8").splitlines():
        url = raw_line.strip()
        if not url or url.startswith("#"):
            continue
        yield url


def fetch_commits(owner, repo, branch, path):
    commits = []
    page = 1
    while True:
        query = urlencode({
            "sha": branch,
            "path": path,
            "per_page": 100,
            "page": page,
        })
        url = f"https://api.github.com/repos/{owner}/{repo}/commits?{query}"
        data, _headers = github_request(url)
        commits.extend(data)
        if len(data) < 100:
            return commits
        page += 1


def first_line(text):
    return text.splitlines()[0] if text else ""


def fetch_commit_detail(owner, repo, sha):
    url = f"https://api.github.com/repos/{owner}/{repo}/commits/{sha}"
    data, _headers = github_request(url)
    return data


def matching_files(detail, path):
    matches = []
    for file_info in detail.get("files", []):
        if file_info.get("filename") == path or file_info.get("previous_filename") == path:
            matches.append(file_info)
    return matches


def write_history(url, owner, repo, branch, path, commits):
    out_file = OUT_DIR / Path(path).name
    tmp_file = out_file.with_name(f".{out_file.name}.tmp")
    history_url = f"https://github.com/{owner}/{repo}/commits/{branch}/{path}"

    with tmp_file.open("w", encoding="utf-8") as output:
        output.write(f"# Historial remoto de {Path(path).name}\n\n")
        output.write(f"- Repositorio: `{owner}/{repo}`\n")
        output.write(f"- Rama: `{branch}`\n")
        output.write(f"- Ruta en repo: `{path}`\n")
        output.write(f"- URL origen: {url}\n")
        output.write(f"- Historial GitHub: {history_url}\n")
        output.write(f"- Commits encontrados: {len(commits)}\n\n")
        if not INCLUDE_PATCHES:
            output.write("> Este fichero lista el historial remoto del documento. ")
            output.write("Para incluir parches por commit ejecuta `INCLUDE_PATCHES=1 ./scripts/export-remote-history.sh`; ")
            output.write("si hay muchos commits conviene usar `GITHUB_TOKEN` para evitar el limite anonimo de GitHub.\n\n")

        for index, commit_item in enumerate(commits, start=1):
            sha = commit_item["sha"]
            commit = commit_item.get("commit", {})
            author = commit.get("author") or {}
            committer = commit.get("committer") or {}
            message = commit.get("message", "")

            print(f"  {index}/{len(commits)} {sha[:7]}")

            output.write("---\n\n")
            output.write(f"## {committer.get('date') or author.get('date', 'sin fecha')} - {first_line(message)}\n\n")
            output.write(f"- Commit: `{sha}`\n")
            output.write(f"- Autor: {author.get('name', 'desconocido')}\n")
            output.write(f"- Enlace: {commit_item.get('html_url', '')}\n\n")

            if message:
                output.write("### Mensaje\n\n")
                output.write("```text\n")
                output.write(message.rstrip())
                output.write("\n```\n\n")

            if not INCLUDE_PATCHES:
                continue

            detail = fetch_commit_detail(owner, repo, sha)
            files = matching_files(detail, path)

            if not files:
                output.write("_GitHub no devolvio el parche de este fichero en el detalle del commit._\n\n")
                continue

            for file_info in files:
                output.write("### Cambio\n\n")
                output.write(f"- Estado: `{file_info.get('status', 'unknown')}`\n")
                if file_info.get("previous_filename"):
                    output.write(f"- Ruta anterior: `{file_info['previous_filename']}`\n")
                output.write(f"- Adiciones: {file_info.get('additions', 0)}\n")
                output.write(f"- Borrados: {file_info.get('deletions', 0)}\n\n")

                patch = file_info.get("patch")
                if patch:
                    output.write("```diff\n")
                    output.write(patch.rstrip())
                    output.write("\n```\n\n")
                else:
                    output.write("_Sin patch disponible en la API para este cambio._\n\n")

    tmp_file.replace(out_file)
    return out_file


processed = 0
skipped = 0

for source_url in read_source_urls():
    parsed = parse_url(source_url)
    if not parsed:
        print(f"Saltando URL no soportada: {source_url}", file=sys.stderr)
        skipped += 1
        continue

    owner, repo, branch, path = parsed
    print(f"Consultando commits de {Path(path).name}...")

    try:
        commits = fetch_commits(owner, repo, branch, path)
        out_file = write_history(source_url, owner, repo, branch, path, commits)
    except RuntimeError as error:
        print(error, file=sys.stderr)
        skipped += 1
        continue

    print(f"Guardado: {out_file}")
    processed += 1
    time.sleep(0.2)

print()
print(f"Documentos procesados: {processed}")
print(f"Documentos omitidos: {skipped}")
print(f"Salida: {OUT_DIR}")
PY
