El opositor quiere generar un test en HTML interactivo alineado con el temario y la oposición. Ejecuta lo siguiente.

## 0. Modo de ejecución silencioso y robusto

- Trabaja en **modo silencioso de cara al opositor**:
  - No narrar búsquedas, lecturas, intentos fallidos, regeneraciones ni validaciones internas.
  - Como máximo, emitir un único mensaje breve inicial si la generación va a tardar, y la respuesta final del apartado 8. Si no es imprescindible, no emitas mensaje inicial.
  - Si surge un problema recuperable, corrígelo internamente sin explicarlo al opositor.
  - Solo informa antes del final si el proceso queda bloqueado y necesitas que el opositor acote materia, reduzca preguntas o aporte material.
- No muestres nunca al opositor el contenido de `test_generados/_test_input.json`, ni completo ni parcial:
  - No cites bloques JSON.
  - No listes preguntas, opciones, respuestas, explicaciones ni fuentes del JSON.
  - No leas ese archivo con una herramienta que vuelque su contenido al chat visible; si necesitas inspeccionarlo, usa validaciones internas por script que sólo devuelvan éxito/fallo o recuentos mínimos.
- Evita que un intento defectuoso llegue al HTML final:
  - Construye y valida primero el JSON.
  - Si detectas distractores mal formados, artículos derogados, duplicados problemáticos o falta de fundamento textual, corrige el JSON antes de ejecutar el generador.
  - No sobrescribas el HTML final hasta que el JSON tenga exactamente **N** preguntas válidas.
- No muestres al opositor salidas de consola, rutas absolutas, trazas de validación, recuentos internos, distribución de respuestas, nombres de scripts ni detalles de depuración. Úsalos solo para decidir si continuar o corregir.

## 1. Número de preguntas y ámbito

- Obtén **N** del mensaje: entero **≥ 1** (p. ej. «10 preguntas», «N = 12»).
- Determina el **ámbito normativo o temático**:
  - Si indica **leyes**: limita el contenido a esos ficheros de `leyes/` (y solo a ellos). El nombre de salida será de tipo **leyes** (véase apartado 7).
  - Si indica **temas** (p. ej. «temas 4, 5 y 22»): lee `utilidades/temario.md`, identifica cada **Tema N** y cruza con los ficheros **existentes** en `leyes/`. Si el tema no es cubrible solo con esos `.md`, dilo y pide acotar temas o ampliar `leyes/` antes de generar. El nombre de salida será de tipo **temas**.
  - Si **no** indica leyes ni temas: aplica **todas** las leyes disponibles en `leyes/` y trata el ámbito como **general** (no hace falta preguntar antes de generar).

**N** y el **ámbito** acordado aplican al resto de instrucciones.

## 2. Rigor: solo leyes del repositorio

- **Única fuente sustantiva** permitida para enunciados, respuestas, explicaciones y distractores: los ficheros **`leyes/*.md`** que correspondan al ámbito elegido (y solo el texto que contienen).
- **Prohibido** incluir datos, plazos, artículos, tipos penales, requisitos o afirmaciones que **no** se puedan localizar o inferir con rigor a partir de esos `.md`.
- Las opciones incorrectas también deben ser contrastables con el mismo texto: inversión de un límite legal explícito, atribución errónea a otro precepto del mismo cuerpo normativo, o formulación que contradiga claramente el precepto citado.
- **No uses** `examenes_oficiales/` ni ningún otro sitio para sustentar contenido. `examenes_oficiales/` y `utilidades/temario.md` pueden orientar formato o ámbito, nunca servir de fuente de verdad normativa.
- Excluye artículos, títulos, libros o fragmentos marcados como **derogados** o que estén dentro de un bloque derogado en el propio `.md` (por ejemplo, un libro completo derogado). No generes preguntas a partir de ellos aunque sigan apareciendo en el fichero.

Si con las leyes disponibles no es posible obtener **N** preguntas rigurosas, reduce N, cambia el ámbito o indica que hace falta acotar la materia o ampliar el material disponible.

## 3. Búsqueda eficiente de fuentes

- No leas una ley completa si supera el tamaño manejable. Usa búsqueda por términos o artículos y luego lee rangos concretos:
  - `rg` para localizar rúbricas, artículos y términos relevantes.
  - `ReadFile` con `offset` y `limit` para leer sólo los rangos necesarios.
- Para N alto, trabaja en bloques de 20-25 preguntas. Tras cada bloque, verifica mentalmente que cada ítem tiene fundamento textual claro.
- Si el ámbito es por temas, usa `utilidades/temario.md` sólo para mapear materia a leyes disponibles; después trabaja únicamente con `leyes/*.md`.
- Para N alto, si usas un script auxiliar para extraer candidatos o montar el JSON, hazlo en una única ejecución controlada y valida su salida antes de generar el HTML. Evita ciclos visibles de “genero, reviso, fallo, regenero”.

## 4. Formato de preguntas

Reproduce el patrón visible de los exámenes oficiales:

- Enunciado como una sola unidad.
- Tres alternativas, una por línea, con texto que empieza por `a)`, `b)`, `c)`.
- Alternativas como proposiciones completas; no uses marcadores vacíos ni «Opción a/b/c».
- Evita distractores gramaticalmente defectuosos o artificiales. En particular, descarta opciones con dobles negaciones accidentales, rangos imposibles o repetidos («dos a dos», «3 y 3»), cambios de categoría absurdos («multa de años» si el precepto habla de prisión), mayúsculas internas por sustitución automática, o frases que suenen a texto roto.
- Si una opción incorrecta se obtiene por variación automática, comprueba que contradice claramente el precepto sin introducir una formulación absurda.
- El HTML final lo genera `opo_scripts/generate_test.py`; no reconstruyas manualmente los `fieldset`, CSS, JavaScript ni objetos `CORRECTAS`.

## 5. Generación estructurada

Antes de crear el HTML, construye un JSON de entrada para el generador. Puede ser un archivo temporal en `test_generados/_test_input.json`; bórralo al terminar si no hace falta conservarlo.

El JSON es un artefacto interno. Nunca debe aparecer en la conversación con el opositor.

Formato del JSON:

```json
{
  "title": "Test Código Penal - 10 preguntas",
  "scope_type": "leyes",
  "scope_id": "codigo-penal",
  "date": "02052026",
  "preguntas": [
    {
      "enunciado": "Según el artículo X, ...:",
      "opciones": {
        "a": "Texto de la opción a.",
        "b": "Texto de la opción b.",
        "c": "Texto de la opción c."
      },
      "correcta": "a",
      "explicacion": "El artículo X establece ...",
      "fuente": "Código Penal, art. X"
    }
  ]
}
```

Reglas del JSON:

- `scope_type`: `general`, `temas` o `leyes`.
- `scope_id`: vacío en `general`; en `temas`, números ordenados unidos por guiones; en `leyes`, slugs ordenados según inventario.
- `date`: formato **DDMMAAAA**.
- `preguntas`: exactamente **N** entradas.
- Cada pregunta debe tener `enunciado`, `opciones.a`, `opciones.b`, `opciones.c`, `correcta`, `explicacion` y, preferiblemente, `fuente`.
- `correcta` debe ser sólo `"a"`, `"b"` o `"c"`.

Antes de ejecutar el generador, valida internamente el JSON:

- exactamente **N** preguntas;
- tres opciones no vacías por pregunta;
- una sola respuesta correcta por pregunta;
- `fuente` presente y coherente con el ámbito;
- ausencia de fragmentos derogados;
- ausencia de distractores con texto roto, duplicado o contradictorio de forma ambigua;
- distribución razonable de respuestas correctas entre `a`, `b` y `c`.

Genera el HTML ejecutando:

```bash
python3 -m opo_scripts.generate_test test_generados/_test_input.json
```

El generador:

- Usa `utilidades/examen-prueba.html` como plantilla de estilo, cronómetro, corrección y repaso.
- Crea los `fieldset`, radios, opción «Sin responder», `CORRECTAS` y `EXPLICACIONES`.
- Valida recuentos y estructura antes de escribir la salida.

## 6. Inventario útil del repositorio

**Exámenes oficiales** (solo formato / estilo; **no** contenido normativo):

- `EXAMEN 2023.md`
- `EXAMEN_TEORIA_INGRESO_ESCALA_EJECUTIVA_36.md`
- `EXAMEN_TEORIA_INSPECTOR_DEPOL_2020.md`
- `EXAMEN_TEORIA_INGRESO_INSPECTOR39_DEPOL_2024.md`
- `EXAMEN_TEORIA_INGRESO_INSPECTOR40_2025_DEPOL_Ingreso.md`

**Leyes** (`leyes/` — única fuente del contenido del test):

| Fichero | Título (según frontmatter) |
|--------|----------------------------|
| `BOE-A-1978-31229.md` | Constitución Española |
| `BOE-A-1995-25444.md` | Ley Orgánica 10/1995 (Código Penal) |
| `BOE-A-2000-544.md` | Ley Orgánica 4/2000 (extranjería e integración social) |
| `BOE-A-2007-4184.md` | Real Decreto 240/2007 (entrada, libre circulación y residencia de ciudadanos UE/EEE) |
| `BOE-A-2015-11719.md` | Texto refundido EBEP (RD Legislativo 5/2015) |
| `BOE-A-2024-24099.md` | Real Decreto 1155/2024 (Reglamento de extranjería) |

## 7. Fichero de salida

- **Directorio:** `test_generados/` (créalo si no existe).
- **Nombre del archivo** (extensión `.html`), **sin espacios**, en minúsculas y sin tildes; al final, siempre la **fecha de generación** en formato **DDMMAAAA** (día, mes y año con cuatro cifras, sin separadores).
  - Ámbito **general** (sin leyes ni temas concretos indicados): `test_general_DDMMAAAA.html`
  - Ámbito **temas**: `test_temas_<identificador>_DDMMAAAA.html`, donde `<identificador>` son los números de tema **ordenados** y unidos por guiones (p. ej. temas 4, 5 y 22 → `4-5-22`).
  - Ámbito **leyes**: `test_leyes_<identificador>_DDMMAAAA.html`, donde `<identificador>` se forma con estos slugs, ordenados según aparezcan en el inventario: `constitucion`, `codigo-penal`, `extranjeria`, `libre-circulacion-ue`, `ebep`, `reglamento-extranjeria`. Si son varias leyes, une los slugs con guiones (p. ej. Constitución + Código Penal → `constitucion-codigo-penal`).
- **Ejemplo:** `test_generados/test_general_02052026.html`
- Si ya existe un archivo con el mismo nombre, **no lo sobrescribas**: añade un sufijo de versión al final, antes de `.html`, empezando por `_01`, luego `_02`, etc.
- Tras generar, valida al menos:
  - recuento de `<fieldset data-q=` igual a **N**;
  - recuento de `value="_skip" checked` igual a **N**;
  - ausencia de errores del generador.

## 7 bis. Registro de intentos

- Si el opositor quiere guardar los resultados de cada intento, antes de abrir el examen debe estar activo el servidor local:

```bash
python3 -m opo_scripts.test_results_server
```

- Al corregir el test, el HTML enviará el intento al servidor y se añadirá una línea en `utilidades/resultados_test.csv`.
- Cada línea registrará: fecha del intento, examen, preguntas respondidas, preguntas sin responder, aciertos, fallos y resultado.
- Si el servidor no está activo, el examen se corrige igualmente, pero el intento no se podrá guardar en el CSV.

No añadas Git ni push salvo que el usuario lo pida en el mismo mensaje.

## 8. Respuesta al opositor

Redacta en **castellano claro**, como si hablaras con la persona que estudia, **sin tecnicismos de proyecto** (nada de rutas absolutas, nombres de ficheros `.md`, identificadores BOE, bloques de código, ni el objeto `CORRECTAS`).

- **No reveles** cuál es la respuesta correcta de ningún ítem ni un resumen de soluciones.
- **No incluyas** letras correctas, claves internas, explicaciones de corrección, fundamentos legales concretos ni referencias de trazabilidad.
- Confirma **cuántas preguntas** tiene el test y el **ámbito** en una frase humana (p. ej. «materia general», «los temas que pediste», «las leyes que indicaste»).
- Di que el examen está guardado en la carpeta **test_generados**, con el **nombre del archivo** (el `.html` generado), y que puede abrirlo con el navegador.
- Si hubo que **reducir N** o **ajustar el ámbito** por falta de norma en el material disponible, explica eso en **una frase** sencilla, sin entrar en detalle técnico.

Antes de responder, revisa mentalmente la salida: debe ser breve, útil para abrir el examen y no debe permitir deducir ninguna solución.
