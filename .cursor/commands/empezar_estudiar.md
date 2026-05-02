Saluda y anima a la opositoria Súper Isis con un tono cercano y motivador.

Después prepara la sesión de estudio siguiendo estos pasos:

1. Arranca el servidor local de resultados de tests en segundo plano, para que los intentos puedan guardarse en `utilidades/resultados_test.csv` cuando la opositoria haga un test:

   ```bash
   python3 -m opo_scripts.test_results_server
   ```

   No esperes a que el comando termine: es un servidor local que debe quedar activo durante la sesión. Si ya está arrancado, no inicies otro duplicado.

2. Actualiza todas las leyes locales:

   ```bash
   ./scripts/update-leyes.sh
   ```

3. Obtén el commit log remoto de cada ley:

   ```bash
   ./scripts/export-remote-history.sh
   ```

4. Lee todos los ficheros de `log_leyes/*.md`.

5. Analiza el commit log de cada ley y entrega un informe muy breve, claro, tranquilo y poco técnico. El objetivo es que Súper Isis sepa qué leyes tienen cambios en su historial remoto y cuál es el último cambio registrado.

   Importante: que `./scripts/update-leyes.sh` diga "Sin cambios" solo significa que el texto descargado hoy no ha cambiado respecto al fichero local. No uses eso para decidir si una ley tiene cambios históricos. La fuente para decidirlo son los ficheros de `log_leyes/`.

   Usa esta estructura en el chat, sin envolverla en bloques de codigo ni usar tablas:

   ¡Vamos, Súper Isis!

   ## Leyes Con Cambios

   - [Nombre claro de la ley]
     Fecha: [fecha de la última actualización]
     Último cambio: [último cambio explicado en una frase breve y orientada al estudio].

   Deja una línea en blanco entre leyes para que el informe respire. Incluye siempre la fecha de la última actualización, no solo el año. Ordena las leyes de más reciente a más antigua según la fecha de última actualización. No menciones leyes cuyo historial no tenga cambios registrados. No añadas consejos generales de estudio, apartados extra ni detalles técnicos.

   Evita mostrar SHAs, comandos, rutas internas, diffs o mensajes técnicos salvo que sean imprescindibles. Traduce los mensajes de commit a lenguaje natural y orientado a estudio.

   Si hubo incidencias al actualizar o consultar GitHub, explícalas al final en lenguaje sencillo y di qué parte del informe puede no estar completa.

Si no detectas leyes con cambios, responde solo con una frase breve indicando que no hay novedades.
