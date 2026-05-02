Saluda y anima a la opositoria Súper Isis con un tono cercano y motivador.

Después prepara la sesión de estudio siguiendo estos pasos:

1. Actualiza todas las leyes locales:

   ```bash
   ./scripts/update-leyes.sh
   ```

2. Obtén el commit log remoto de cada ley:

   ```bash
   ./scripts/export-remote-history.sh
   ```

3. Lee todos los ficheros de `log_leyes/*.md`.

4. Analiza el commit log de cada ley y entrega un informe muy breve, claro, tranquilo y poco técnico. El objetivo es que Súper Isis sepa qué leyes tienen cambios en su historial remoto y cuál es el último cambio registrado.

   Importante: que `./scripts/update-leyes.sh` diga "Sin cambios" solo significa que el texto descargado hoy no ha cambiado respecto al fichero local. No uses eso para decidir si una ley tiene cambios históricos. La fuente para decidirlo son los ficheros de `log_leyes/`.

   Usa esta estructura como texto normal en el chat, sin envolverla en bloques de codigo, tablas ni Markdown incrustado:

   ¡Vamos, Súper Isis!

   Leyes con cambios:
   [Nombre o identificador de la ley] - [fecha de la última actualización]: [último cambio explicado en una frase].

   Incluye siempre la fecha de la última actualización, no solo el año. No menciones leyes cuyo historial no tenga cambios registrados. No añadas consejos generales de estudio, apartados extra ni detalles técnicos.

   Evita mostrar SHAs, comandos, rutas internas, diffs o mensajes técnicos salvo que sean imprescindibles. Traduce los mensajes de commit a lenguaje natural y orientado a estudio.

   Si hubo incidencias al actualizar o consultar GitHub, explícalas al final en lenguaje sencillo y di qué parte del informe puede no estar completa.

Si no detectas leyes con cambios, responde solo con una frase breve indicando que no hay novedades.
