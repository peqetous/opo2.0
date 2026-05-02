#!/usr/bin/env bash
set -euo pipefail

LIST_FILE="${1:-example.txt}"
DEST_DIR="${2:-leyes}"

if [[ ! -f "$LIST_FILE" ]]; then
  echo "No existe el archivo de lista: $LIST_FILE" >&2
  exit 1
fi

mkdir -p "$DEST_DIR"

changed_files=()
checked_count=0

to_raw_url() {
  local url="$1"

  if [[ "$url" =~ ^https://raw\.githubusercontent\.com/ ]]; then
    printf '%s\n' "$url"
    return
  fi

  if [[ "$url" =~ ^https://github\.com/([^/]+)/([^/]+)/blob/([^/]+)/(.+)$ ]]; then
    printf 'https://raw.githubusercontent.com/%s/%s/%s/%s\n' \
      "${BASH_REMATCH[1]}" \
      "${BASH_REMATCH[2]}" \
      "${BASH_REMATCH[3]}" \
      "${BASH_REMATCH[4]}"
    return
  fi

  printf '%s\n' "$url"
}

while IFS= read -r line || [[ -n "$line" ]]; do
  url="$(printf '%s' "$line" | sed 's/[[:space:]]*$//')"

  # Ignora vacias y comentarios.
  if [[ -z "$url" || "$url" == \#* ]]; then
    continue
  fi

  raw_url="$(to_raw_url "$url")"
  file_name="$(basename "$raw_url")"
  target_file="$DEST_DIR/$file_name"
  tmp_file="$(mktemp)"

  checked_count=$((checked_count + 1))
  echo "Descargando: $file_name"

  if ! curl -fsSL "$raw_url" -o "$tmp_file"; then
    echo "  Error al descargar: $raw_url" >&2
    rm -f "$tmp_file"
    continue
  fi

  if [[ -f "$target_file" ]] && cmp -s "$tmp_file" "$target_file"; then
    echo "  Sin cambios"
    rm -f "$tmp_file"
    continue
  fi

  mv "$tmp_file" "$target_file"
  changed_files+=("$target_file")
  echo "  Actualizado"
done < "$LIST_FILE"

echo
echo "Revisados: $checked_count"
echo "Actualizados: ${#changed_files[@]}"

if (( ${#changed_files[@]} > 0 )); then
  echo "Archivos actualizados:"
  printf ' - %s\n' "${changed_files[@]}"
fi
