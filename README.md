# OPO 2.0

Herramientas locales para descargar textos legales desde `legalize-dev/legalize-es` y exportar el historial remoto de cambios de cada documento.

## Archivos principales

- `example.txt`: lista de URLs de documentos a consultar.
- `leyes/`: copias locales actualizadas de los documentos.
- `log_leyes/`: ficheros Markdown con el historial remoto de commits de cada documento.
- `scripts/update-leyes.sh`: descarga o actualiza las leyes locales.
- `scripts/export-remote-history.sh`: exporta el historial remoto de cambios.

## Descargar o actualizar leyes

Ejecuta:

```bash
./scripts/update-leyes.sh
```

El script lee `example.txt` y guarda cada documento en `leyes/`.

También puedes indicar otra lista de URLs y otra carpeta de salida:

```bash
./scripts/update-leyes.sh example.txt leyes
```

## Comando de Cursor para estudiar

Puedes iniciar una sesion de estudio desde Cursor con:

```text
/empezar_estudiar
```

El comando saluda y anima a Super Isis, actualiza las leyes, exporta el historial remoto de commits de cada ley y pide a la IA que revise esos historiales para indicar si hay cambios recientes relevantes.

## Exportar historial remoto de cambios

Ejecuta:

```bash
./scripts/export-remote-history.sh
```

El script lee `example.txt`, consulta GitHub por cada documento y genera un `.md` por ley en `log_leyes/`.

También puedes indicar otra lista de URLs y otra carpeta de salida:

```bash
./scripts/export-remote-history.sh example.txt log_leyes
```

## Evitar limites de GitHub

GitHub limita las peticiones anonimas. Si tienes GitHub CLI autenticado, el script usa automaticamente `gh auth token` para hacer las peticiones autenticadas:

```bash
gh auth login -h github.com
./scripts/export-remote-history.sh
```

Tambien puedes pasar un token personal explicitamente:

```bash
GITHUB_TOKEN=tu_token ./scripts/export-remote-history.sh
```

## Incluir parches por commit

Por defecto el historial exportado incluye fecha, autor, SHA, enlace y mensaje de commit. Para incluir tambien el diff/patch de cada cambio:

```bash
INCLUDE_PATCHES=1 ./scripts/export-remote-history.sh
```

Esta opcion hace mas peticiones a GitHub, por eso es recomendable usar GitHub CLI autenticado o `GITHUB_TOKEN`.

## Revisar cambios con Git

Despues de actualizar leyes o historiales:

```bash
git status
git diff -- leyes/ log_leyes/
```

Para guardar una actualizacion:

```bash
git add example.txt leyes log_leyes scripts README.md
git commit -m "chore: actualizar leyes e historiales legales"
```
