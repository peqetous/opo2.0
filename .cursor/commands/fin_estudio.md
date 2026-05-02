El opositor indica qué temas ha estudiado hoy (por ejemplo: «Tema 1, Tema 14 y tema 15»). Ejecuta lo siguiente en orden.

## 1. Registrar en la bitácora

- **Fichero:** `utilidades/bitacora.md` (bitácora del estudio; no uses otro nombre de ruta).
- **Fecha de hoy:** día/mes/año en formato numérico con ceros a la izquierda si aplica (ej. `02/05/2026`). Usa la fecha local del sistema donde corre el entorno.
- **Temas:** extrae los números de tema del mensaje del usuario (normaliza «Tema», «tema», «TEMA», etc.). Construye un array de enteros únicos, ordenados de menor a mayor (ej. `[1, 14, 15]`).

**Formato de cada día** (append al final del fichero; si el fichero está vacío, añade antes una línea `# Bitácora de estudio` y una línea en blanco):

- Encabezado de segundo nivel: `## DD/MM/AAAA`
- Línea en blanco
- Un bloque de código etiquetado como `yaml` con exactamente estas claves: `fecha` (string `DD/MM/AAAA`) y `temas` (lista de enteros, p. ej. `[1, 14, 15]`).

Si **ya existe** una sección `## DD/MM/AAAA` para la fecha de hoy, no dupliques el encabezado: actualiza solo el bloque `yaml` de ese día fusionando los temas ya guardados con los números nuevos (unión, sin duplicados, orden ascendente).

## 2. Git: cambios y subida a `main`

1. Ejecuta `git status` en la raíz del repositorio.
2. Si hay **cualquier** cambio (tracked o untracked), inclúyelo **todo** en el commit: desde la raíz del repo ejecuta `git add -A` (respeta `.gitignore`; no fuerces ficheros ignorados). No limites el stage a la bitácora ni a un subconjunto arbitrario: el remoto debe reflejar el estado completo del trabajo local pendiente.
3. Si tras el `git add -A` hay algo que commitear, crea **un** commit con mensaje claro en español centrado en la sesión de estudio de hoy (ej. `Bitácora: temas estudiados DD/MM/AAAA`), aunque el commit agrupe también otros ficheros modificados ese día.
4. Asegúrate de estar en la rama `main`.
5. Ejecuta `git push origin main` (o `git push -u origin main` si aún no hay upstream). Si el push falla (sin credenciales, remoto caído, conflictos), explica al usuario qué ocurrió y qué puede hacer, sin inventar que se subió si no fue así.

## 3. Respuesta al opositor

Confirma en una frase qué temas quedaron registrados para hoy y que **todos** los cambios del repositorio quedaron subidos a `main` en remoto (o el error concreto si no pudo subirse). Tono cercano y breve, alineado con la sesión de oposición.
