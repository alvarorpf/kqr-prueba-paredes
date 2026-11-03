# kqr-prueba-paredes · Prueba técnica Odoo 19

Aquí está mi entrega: el módulo [`arpf_sscc_palet`](./arpf_sscc_palet/README.md) para la Parte 1 y mis respuestas a la Parte 2 en [`RESPUESTAS.md`](./RESPUESTAS.md).

## Decisiones
- **Hice que la unicidad fuera de toda la tabla y no solo por compañía.** Con los prefijos del enunciado, el de A (8412345) es el inicio del de B (841234567), así que A con el serial 670000001 generaría el mismo SSCC que B con 0000001. Dejé un test que lo comprueba.
- **Tomo la compañía del entorno y no del palet**, porque en Odoo 19 un palet vacío no tiene compañía: se calcula a partir de lo que contiene.
- **Cada compañía tiene su propia secuencia** en PostgreSQL, así no se pisan aunque dos personas creen palets al mismo tiempo.
- **Algunas cosas las supuse:** que la extensión siempre es 0, que el serial empieza en 1, que el prefijo tiene entre 6 y 12 dígitos, y que si alguien crea un palet en una compañía sin prefijo es mejor que falle con un mensaje claro a que el palet se quede sin SSCC. Esto último es decisión mía y me gustaría validarlo con ustedes.
- En la Parte 2 respondí qué haría en cada caso, sin escribir código.

## Uso de IA
- Trabajé con Claude Code (Sonnet 5.5), que escribió el módulo, los tests y los documentos. Yo marqué el rumbo (nombre del módulo, qué entregar y qué dejar fuera) y le pedí levantar un Odoo 19 y probar el flujo en el navegador con Playwright.
- Por iniciativa propia, Claude comprobó las APIs contra el código fuente de Odoo 19 y recalculó a mano los dígitos de control, y un segundo agente revisó el módulo (de ahí salen los dos límites de Pendiente). Los primeros tests fallaron 3 veces y se corrigieron: las secuencias de PostgreSQL no se revierten entre tests, y un `size` en el campo recortaba el prefijo sin avisar.

## Pendiente
- Quedaron fuera, como indica el enunciado, la etiqueta en PDF y la migración de los palets que ya existían (que se quedan sin SSCC). En RESPUESTAS.md tampoco incluí las preguntas que le haría al cliente.
- Las respuestas de la Parte 2 las contrasté con el código fuente de Odoo, pero no en una instancia en marcha. Con más tiempo agregaría la búsqueda por SSCC en la lista de palets y programaría el wizard del punto 1.
- Hay dos límites que conozco: con varias compañías activas, el prefijo sale de la compañía actual, que puede no coincidir con la del contenido del palet (esto no tiene test), y los palets creados antes de instalar el módulo no se pueden rellenar después.

## Tests
- Los corro desde `/media/camus/ARCHIVOS/odoo19/odoo`, con una base nueva: `/media/camus/ARCHIVOS/odoo19/venv-19/bin/python odoo-bin -c /tmp/arpf_tmp.conf -d arpf_sscc_tmp -i arpf_sscc_palet --test-tags /arpf_sscc_palet --without-demo=all --stop-after-init --log-level=test`. El `.conf` solo lleva los datos de la base y el `addons_path`, con `odoo/addons` y la raíz de este repo.
- El resultado es `0 failed, 0 error(s) of 15 tests`, y el módulo se instala sin errores ni warnings. Lo volví a ejecutar antes de entregar.
