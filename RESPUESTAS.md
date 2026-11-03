# Parte 2 — ¿Configurar o desarrollar?

Odoo 19. Las referencias `archivo:línea` son del código fuente de Odoo 19 que se revisó para responder.

## 1. Fabricante de maquinaria — añadir un bloque (sección + productos) a un presupuesto con líneas

- **Decisión:** desarrollo a medida, pequeño. La plantilla estándar no sirve: al aplicarla Odoo hace `Command.clear()` y sustituye todas las líneas (`sale_management/models/sale_order.py:91`).
- **Qué se haría:** primero buscar un módulo OCA/Apps que *añada* plantillas; si no existe, un wizard "Añadir bloque" que cree las líneas de la plantilla (sección + productos, con `_prepare_order_line_values()`) con `sequence` posterior a la última línea, sin borrar nada.

## 2. Fabricante de alimentación — el TPV no debe pedir lote, las recepciones sí

- **Decisión:** configuración estándar, sin desarrollo.
- **Qué se haría:** el TPV solo pide lote si su tipo de operación tiene "Create New Lots/Serial Numbers" o "Use Existing Lots/Serial Numbers" (`point_of_sale/static/src/app/models/product_template.js:28`). Se desmarcan ambas **solo en el tipo de operación del TPV**; el producto sigue con seguimiento por lote, así que recepciones y producción siguen exigiéndolo. La venta de tienda descuenta el lote según la estrategia de salida (FEFO/FIFO).

## 3. Migración de CRM — 4.000 clientes, NIF de Chile, México y Colombia rechazados

- **Decisión:** script puntual de importación; no se desactiva la validación (no hay un interruptor global, y quitarla dejaría NIF inválidos para la facturación electrónica de toda la base).
- **Qué se haría:** 1º normalizar el Excel (puntos, guiones, espacios, dígito verificador, país informado) e importar por la vía estándar; 2º los rechazados que el cliente confirme como válidos se cargan por script/RPC con el contexto `no_vat_validation=True` **solo en esa carga** (`base_vat/models/res_partner.py:144`), entregando la lista de excepciones.
