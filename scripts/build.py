#!/usr/bin/env python3
"""
Genera el catálogo a partir de data/productos.csv y data/config.json.

Salidas:
  index.html               -> se actualizan los bloques <!-- build:head --> y <!-- build:data -->
  img/<id>.webp            -> imagen optimizada para el sitio
  img/og/<id>.jpg          -> imagen 1200x630 para vista previa en WhatsApp
  img/og/portada.jpg       -> vista previa de la página principal
  p/<id>/index.html        -> enlace compartible por producto (con vista previa)
  feed/meta-catalogo.csv   -> feed para el catálogo de WhatsApp Business / Meta Commerce Manager
  sitemap.xml, robots.txt

Uso: python scripts/build.py
"""
import csv, hashlib, html, io, json, re, sys, unicodedata, urllib.request
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parent.parent
DATA, IMG = ROOT / "data", ROOT / "img"
SRC_IMG, OG_DIR = IMG / "originales", IMG / "og"
CACHE_FILE = IMG / ".cache.json"
GENEROS = {"caballero": "Caballero", "hombre": "Caballero", "dama": "Dama", "mujer": "Dama", "unisex": "Unisex"}
SI = {"si", "sí", "s", "yes", "y", "1", "x", "true"}

errores, avisos = [], []


def slug(texto):
    t = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-")


def leer_csv(ruta):
    raw = ruta.read_bytes()
    for enc in ("utf-8-sig", "cp1252"):  # Excel en Windows guarda en cp1252 si no se elige "CSV UTF-8"
        try:
            texto = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    delim = ";" if texto.splitlines()[0].count(";") > texto.splitlines()[0].count(",") else ","
    return list(csv.DictReader(io.StringIO(texto), delimiter=delim))


def precio(valor, fila, campo):
    v = (valor or "").strip().replace("$", "").replace(",", "").replace(" ", "")
    if not v:
        return None
    try:
        return round(float(v), 2)
    except ValueError:
        errores.append(f"Fila {fila}: '{campo}' no es un número ({valor})")
        return None


def url_imagen(v):
    """Convierte enlaces de Google Drive (compartir/abrir/uc/thumbnail) a una URL descargable."""
    m = re.search(r"drive\.google\.com/(?:file/d/|open\?id=|uc\?(?:export=\w+&)?id=|thumbnail\?id=)([\w-]+)", v)
    return f"https://drive.google.com/thumbnail?id={m.group(1)}&sz=w1200" if m else v


def descargar(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (catalogo-build)"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def procesar_imagen(p, cache):
    """Genera img/<id>.webp e img/og/<id>.jpg. Devuelve la ruta relativa usada por el sitio."""
    origen = (p.pop("_imagen") or "").strip()
    if not origen:
        avisos.append(f"{p['id']}: sin imagen")
        return ""
    remoto = origen.startswith("http")
    if remoto:
        firma = url_imagen(origen)
    else:
        archivo = SRC_IMG / origen
        if not archivo.exists():
            errores.append(f"{p['id']}: no existe img/originales/{origen}")
            return ""
        firma = f"{origen}:{archivo.stat().st_size}:{int(archivo.stat().st_mtime)}"
    webp, og = IMG / f"{p['id']}.webp", OG_DIR / f"{p['id']}.jpg"
    if cache.get(p["id"]) == firma and webp.exists() and og.exists():
        return f"img/{webp.name}"
    try:
        datos = descargar(firma) if remoto else archivo.read_bytes()
        im = ImageOps.exif_transpose(Image.open(io.BytesIO(datos)))
    except Exception as e:  # sin conexión o enlace privado: se usa la URL remota
        avisos.append(f"{p['id']}: no se pudo obtener la imagen ({e}); se usa el enlace directo")
        return firma if remoto else ""
    if im.mode in ("RGBA", "LA", "P"):
        fondo = Image.new("RGB", im.size, (255, 255, 255))
        im = im.convert("RGBA")
        fondo.paste(im, mask=im.split()[-1])
        im = fondo
    else:
        im = im.convert("RGB")
    im.thumbnail((1000, 1000), Image.LANCZOS)
    im.save(webp, "WEBP", quality=86, method=6)
    lienzo = Image.new("RGB", (1200, 630), (245, 245, 247))
    copia = im.copy()
    copia.thumbnail((1100, 560), Image.LANCZOS)
    lienzo.paste(copia, ((1200 - copia.width) // 2, (630 - copia.height) // 2))
    lienzo.save(og, "JPEG", quality=85, optimize=True)
    cache[p["id"]] = firma
    return f"img/{webp.name}"


def portada(productos, cfg):
    """Imagen 1200x630 para compartir la página principal."""
    lienzo = Image.new("RGB", (1200, 630), (245, 245, 247))
    d = ImageDraw.Draw(lienzo)
    try:
        f1, f2 = ImageFont.load_default(size=64), ImageFont.load_default(size=30)
    except TypeError:
        f1 = f2 = ImageFont.load_default()
    d.text((70, 90), cfg["tienda"], fill=(29, 29, 31), font=f1)
    d.text((70, 180), cfg["titulo"], fill=(60, 60, 67), font=f2)
    d.text((70, 225), f"{len(productos)} fragancias disponibles", fill=(110, 110, 115), font=f2)
    fotos = [IMG / f"{p['id']}.webp" for p in productos if (IMG / f"{p['id']}.webp").exists()][:6]
    for i, f in enumerate(fotos):
        im = Image.open(f).convert("RGB")
        im.thumbnail((220, 220), Image.LANCZOS)
        x, y = 560 + (i % 3) * 205, 40 + (i // 3) * 280
        tarjeta = Image.new("RGB", (190, 260), (255, 255, 255))
        tarjeta.paste(im, ((190 - im.width) // 2, (260 - im.height) // 2))
        lienzo.paste(tarjeta, (x, y))
    d.rounded_rectangle((70, 470, 470, 540), 35, fill=(37, 211, 102))
    d.text((105, 487), "Pide por WhatsApp", fill=(255, 255, 255), font=f2)
    lienzo.save(OG_DIR / "portada.jpg", "JPEG", quality=85, optimize=True)


def reemplazar_bloque(texto, nombre, contenido):
    patron = re.compile(rf"(<!-- build:{nombre} -->)(.*?)(<!-- /build:{nombre} -->)", re.S)
    if not patron.search(texto):
        errores.append(f"index.html no tiene el bloque build:{nombre}")
        return texto
    return patron.sub(lambda m: f"{m.group(1)}\n{contenido}\n    {m.group(3)}", texto)


def main():
    cfg = json.loads((DATA / "config.json").read_text(encoding="utf-8"))
    base = cfg["url_base"].rstrip("/") + "/"
    cfg["whatsapp"] = re.sub(r"\D", "", cfg["whatsapp"])  # wa.me requiere solo dígitos

    if cfg.get("sheet_csv_url"):
        try:
            (DATA / "productos.csv").write_bytes(descargar(cfg["sheet_csv_url"]))
            print("Catálogo descargado de Google Sheets")
        except Exception as e:
            avisos.append(f"No se pudo leer Google Sheets ({e}); se usa data/productos.csv")

    OG_DIR.mkdir(parents=True, exist_ok=True)
    SRC_IMG.mkdir(parents=True, exist_ok=True)
    cache = json.loads(CACHE_FILE.read_text()) if CACHE_FILE.exists() else {}

    productos, ids = [], set()
    for n, f in enumerate(leer_csv(DATA / "productos.csv"), start=2):
        f = {k.strip().lower(): (v or "").strip() for k, v in f.items() if k}
        if not any(f.values()):
            continue
        marca, nombre = f.get("marca", ""), f.get("nombre", "")
        if not marca or not nombre:
            errores.append(f"Fila {n}: falta marca o nombre")
            continue
        genero = GENEROS.get(f.get("genero", "").lower())
        if not genero:
            errores.append(f"Fila {n}: genero debe ser caballero, dama o unisex (vino '{f.get('genero')}')")
            continue
        ml = re.sub(r"\D", "", f.get("ml", ""))
        pid = slug(f.get("id") or f"{marca} {nombre} {ml}")
        if pid in ids:
            errores.append(f"Fila {n}: producto duplicado ({pid})")
            continue
        ids.add(pid)
        p = {
            "id": pid, "marca": marca, "nombre": nombre, "ml": int(ml) if ml else None,
            "genero": genero, "presentacion": f.get("presentacion", ""),
            "precio": precio(f.get("precio"), n, "precio"),
            "precio_oferta": precio(f.get("precio_oferta"), n, "precio_oferta"),
            "disponible": f.get("disponible", "si").lower() not in {"no", "0", "agotado"},
            "etiquetas": [e.strip() for e in re.split(r"[|;/]", f.get("etiquetas", "")) if e.strip()],
            "familia": f.get("familia", ""), "descripcion": f.get("descripcion", ""),
            "destacado": f.get("destacado", "").lower() in SI, "_imagen": f.get("imagen", ""),
        }
        p["imagen"] = procesar_imagen(p, cache)
        productos.append(p)

    if errores:
        print("\nERRORES (corrige data/productos.csv):\n  - " + "\n  - ".join(errores))
        sys.exit(1)

    CACHE_FILE.write_text(json.dumps(cache, indent=1, sort_keys=True))
    vigentes = {p["id"] for p in productos}
    for f in list(IMG.glob("*.webp")) + [x for x in OG_DIR.glob("*.jpg") if x.stem != "portada"]:
        if f.stem not in vigentes:
            f.unlink()
    portada(productos, cfg)

    # ---- index.html ----
    idx = ROOT / "index.html"
    version = hashlib.sha1(b"".join((ROOT / "assets" / a).read_bytes() for a in ("styles.css", "app.js"))).hexdigest()[:8]
    esc = lambda s: html.escape(s, quote=True)
    desc = f"{cfg['subtitulo']} {len(productos)} fragancias de {len({p['marca'] for p in productos})} marcas."
    head = f"""    <title>{esc(cfg['tienda'])} | {esc(cfg['titulo'])}</title>
    <meta name="description" content="{esc(desc)}">
    <link rel="canonical" href="{base}">
    <meta property="og:type" content="website">
    <meta property="og:site_name" content="{esc(cfg['tienda'])}">
    <meta property="og:title" content="{esc(cfg['tienda'])} | {esc(cfg['titulo'])}">
    <meta property="og:description" content="{esc(desc)}">
    <meta property="og:url" content="{base}">
    <meta property="og:image" content="{base}img/og/portada.jpg">
    <meta property="og:image:width" content="1200">
    <meta property="og:image:height" content="630">
    <meta name="twitter:card" content="summary_large_image">
    <link rel="stylesheet" href="assets/styles.css?v={version}">
    <script defer src="assets/app.js?v={version}"></script>"""
    publico = {k: v for k, v in cfg.items() if k != "sheet_csv_url"}
    datos = json.dumps({"config": publico, "productos": productos}, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    texto = idx.read_text(encoding="utf-8")
    texto = reemplazar_bloque(texto, "head", head)
    texto = reemplazar_bloque(texto, "data", f'    <script id="catalogo" type="application/json">{datos}</script>')
    if errores:
        print("\n".join(errores)); sys.exit(1)
    idx.write_text(texto, encoding="utf-8")

    # ---- páginas compartibles por producto ----
    pdir = ROOT / "p"
    if pdir.exists():
        for d in pdir.iterdir():
            if d.is_dir() and d.name not in vigentes:
                for x in d.iterdir():
                    x.unlink()
                d.rmdir()
    mon = cfg.get("moneda", "MXN")
    for p in productos:
        titulo = f"{p['marca']} {p['nombre']}" + (f" {p['ml']} ml" if p["ml"] else "")
        valor = p["precio_oferta"] or p["precio"]
        d = f"{p['genero']}. " + (f"${valor:,.0f} {mon}. " if valor else "") + ("Disponible. " if p["disponible"] else "Agotado. ") + "100% original. Pídelo por WhatsApp."
        img = f"{base}img/og/{p['id']}.jpg" if (OG_DIR / f"{p['id']}.jpg").exists() else f"{base}img/og/portada.jpg"
        precio_meta = f'\n<meta property="product:price:amount" content="{valor:.2f}">\n<meta property="product:price:currency" content="{mon}">' if valor else ""
        destino = f"../../?p={p['id']}"
        (pdir / p["id"]).mkdir(parents=True, exist_ok=True)
        (pdir / p["id"] / "index.html").write_text(f"""<!DOCTYPE html>
<html lang="es"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(titulo)} | {esc(cfg['tienda'])}</title>
<meta name="description" content="{esc(d)}">
<link rel="canonical" href="{base}p/{p['id']}/">
<meta property="og:type" content="product">
<meta property="og:site_name" content="{esc(cfg['tienda'])}">
<meta property="og:title" content="{esc(titulo)}">
<meta property="og:description" content="{esc(d)}">
<meta property="og:url" content="{base}p/{p['id']}/">
<meta property="og:image" content="{img}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">{precio_meta}
<meta name="twitter:card" content="summary_large_image">
<script>location.replace("{destino}"+(location.search?"&"+location.search.slice(1):""))</script>
</head><body><a href="{destino}">Ver {esc(titulo)}</a></body></html>
""", encoding="utf-8")

    # ---- feed para catálogo de WhatsApp Business (Meta Commerce Manager) ----
    (ROOT / "feed").mkdir(exist_ok=True)
    con_precio = [p for p in productos if p["precio"]]
    with open(ROOT / "feed" / "meta-catalogo.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["id", "title", "description", "availability", "condition", "price", "sale_price", "link", "image_link", "brand"])
        for p in con_precio:
            titulo = f"{p['marca']} {p['nombre']}" + (f" {p['ml']} ml" if p["ml"] else "")
            w.writerow([
                p["id"], titulo[:150],
                p["descripcion"] or f"{titulo}. Perfume original para {p['genero'].lower()}.",
                "in stock" if p["disponible"] else "out of stock", "new",
                f"{p['precio']:.2f} {mon}", f"{p['precio_oferta']:.2f} {mon}" if p["precio_oferta"] else "",
                f"{base}p/{p['id']}/",
                f"{base}img/og/{p['id']}.jpg" if (OG_DIR / f"{p['id']}.jpg").exists() else p["imagen"],
                p["marca"],
            ])
    if len(con_precio) < len(productos):
        avisos.append(f"{len(productos) - len(con_precio)} productos sin precio no se incluyen en feed/meta-catalogo.csv (Meta exige precio)")

    # ---- sitemap y robots ----
    urls = [base] + [f"{base}p/{p['id']}/" for p in productos]
    (ROOT / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
                                      + "".join(f"  <url><loc>{u}</loc></url>\n" for u in urls) + "</urlset>\n", encoding="utf-8")
    (ROOT / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {base}sitemap.xml\n", encoding="utf-8")

    print(f"OK: {len(productos)} productos, {len(con_precio)} en feed de Meta.")
    for a in avisos:
        print("  aviso:", a)


if __name__ == "__main__":
    main()
