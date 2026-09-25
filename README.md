# STÉLUM · Catálogo de perfumes

Sitio: https://stelummx.github.io/catalogo-perfumes/

El catálogo se genera solo a partir de **`data/productos.csv`**. No hay que tocar HTML para agregar productos.

## Agregar o editar productos (2 minutos)

1. Sube la foto a `img/originales/` (PNG o JPG, fondo claro). En GitHub: *Add file > Upload files*.
   También puedes pegar un enlace de Google Drive en la columna `imagen` (el archivo debe estar compartido como "Cualquier persona con el enlace").
2. Edita `data/productos.csv` (lápiz en GitHub) y agrega una fila.
3. *Commit changes*. En 1 a 2 minutos la acción **Actualizar catálogo** optimiza imágenes, genera las páginas y publica.

Si hay un error (por ejemplo, un género mal escrito), la acción falla en la pestaña *Actions* y el mensaje dice qué fila corregir.

### Columnas

| columna | obligatorio | ejemplo | notas |
|---|---|---|---|
| marca | sí | Versace | |
| nombre | sí | Eros Eau de Parfum | |
| ml | | 100 | |
| genero | sí | caballero / dama / unisex | |
| presentacion | | Nuevo, Tester, Set | aparece como etiqueta y en el mensaje de WhatsApp |
| precio | | 1899 | vacío = "Precio por WhatsApp" |
| precio_oferta | | 1599 | muestra el descuento en % |
| disponible | | si / no | "no" = Agotado, botón "Avisarme cuando llegue" |
| etiquetas | | lanzamiento\|mas vendido | separadas por `\|` |
| familia | | Amaderada | familia olfativa |
| descripcion | | Notas de salida... | se ve en el detalle |
| imagen | | versace-eros.png o enlace de Drive | archivo dentro de `img/originales/` |
| destacado | | si | sale primero |
| id | | | opcional; si no, se genera de marca+nombre+ml |

Si editas en Excel, guarda como **CSV UTF-8**. El script también acepta `;` como separador.

### Opción: editar desde Google Sheets

1. Crea una hoja con las mismas columnas.
2. *Archivo > Compartir > Publicar en la web > CSV* y copia el enlace.
3. Pégalo en `data/config.json` en `sheet_csv_url`.

La acción revisa la hoja cada 6 horas. Para publicar al momento: *Actions > Actualizar catálogo > Run workflow* (funciona desde el celular).

## Campañas de WhatsApp

Cada producto tiene un enlace con vista previa (foto, nombre y precio) al compartirlo:

```
https://stelummx.github.io/catalogo-perfumes/p/<id>/
```

Enlaces útiles para difusiones y estados:

| qué | enlace |
|---|---|
| producto | `.../p/versace-eros-eau-de-parfum-100/` |
| solo dama | `.../?genero=dama` |
| una marca | `.../?marca=Versace` |
| búsqueda | `.../?q=eros` |
| medir campaña | agrega `?c=nombre` (o `&c=` si ya hay `?`) |

Con `c=` el mensaje que te llega por WhatsApp termina con `(ref: nombre)`, así sabes de qué campaña vino cada cliente.
El botón **Compartir** de cada producto copia su enlace.

### Catálogo de WhatsApp Business

`feed/meta-catalogo.csv` se genera con los productos que tienen precio. En Meta Commerce Manager: *Catálogo > Orígenes de datos > Feed de datos > URL programada* con:

```
https://stelummx.github.io/catalogo-perfumes/feed/meta-catalogo.csv
```

Así el catálogo de WhatsApp Business se sincroniza solo con el sitio.

## Configuración (`data/config.json`)

`whatsapp` (solo dígitos, con 52), textos del encabezado, sellos de confianza, `envios` y `pagos` (si los llenas aparece la pregunta frecuente), `instagram`.

## Estructura

```
data/productos.csv     fuente del catálogo (editar aquí)
data/config.json       datos de la tienda
img/originales/        fotos originales (subir aquí)
assets/                estilos y lógica del sitio
scripts/build.py       generador
.github/workflows/     automatización
-- generados, no editar --
index.html (bloques build), img/*.webp, img/og/, p/, feed/, sitemap.xml
```

Probar local: `pip install pillow && python scripts/build.py && python -m http.server` y abrir http://localhost:8000
