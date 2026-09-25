/* STÉLUM · Catálogo. Los datos vienen de <script id="catalogo">, generado por scripts/build.py */
(() => {
    "use strict";
    const $ = (s) => document.querySelector(s);
    const { config: cfg, productos } = JSON.parse($("#catalogo").textContent);
    const params = new URLSearchParams(location.search);
    // Atribución de campaña: ?c=nombre o ?utm_campaign=nombre se añade al mensaje de WhatsApp
    const campana = params.get("c") || params.get("utm_campaign") || "";
    const base = cfg.url_base.replace(/\/?$/, "/");
    const money = new Intl.NumberFormat("es-MX", { style: "currency", currency: cfg.moneda || "MXN", maximumFractionDigits: 0 });
    const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
    const norm = (s) => String(s).normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
    const titulo = (p) => `${p.marca} ${p.nombre}${p.ml ? ` ${p.ml} ml` : ""}`;
    const icon = '<svg class="i-wa" viewBox="0 0 448 512" aria-hidden="true"><use href="#wa"/></svg>';

    function wa(texto) {
        const ref = campana ? `\n(ref: ${campana})` : "";
        return `https://wa.me/${cfg.whatsapp}?text=${encodeURIComponent(texto + ref)}`;
    }
    const waProducto = (p) => wa(`Hola, me interesa el perfume ${titulo(p)}${p.presentacion ? ` (${p.presentacion})` : ""}. ¿Está disponible?\n${base}p/${p.id}/`);

    function precioHTML(p) {
        if (!p.disponible) return '<span class="price price--ask">Agotado · pregunta por reabasto</span>';
        if (p.precio_oferta && p.precio) return `<span class="price">${money.format(p.precio_oferta)}<s>${money.format(p.precio)}</s></span>`;
        if (p.precio) return `<span class="price">${money.format(p.precio)}</span>`;
        return '<span class="price price--ask">Precio por WhatsApp</span>';
    }
    function chipsHTML(p) {
        return [p.ml && `${p.ml} ml`, p.genero, p.presentacion, p.familia].filter(Boolean).map((c) => `<span class="chip">${esc(c)}</span>`).join("");
    }
    function badgesHTML(p) {
        const b = p.etiquetas.map((e) => `<span class="badge">${esc(e)}</span>`);
        if (p.precio_oferta && p.precio) b.unshift(`<span class="badge badge--oferta">-${Math.round((1 - p.precio_oferta / p.precio) * 100)}%</span>`);
        if (!p.disponible) b.unshift('<span class="badge badge--agotado">Agotado</span>');
        return b.length ? `<span class="badges">${b.join("")}</span>` : "";
    }
    const img = (p, cls = "") => p.imagen
        ? `<img src="${esc(p.imagen)}" alt="${esc(titulo(p))}" loading="lazy" decoding="async" width="400" height="340" ${cls} onerror="this.replaceWith(Object.assign(document.createElement('span'),{className:'ph',textContent:'Imagen no disponible'}))">`
        : '<span class="ph">Imagen próximamente</span>';

    // ---- Estado y filtros ----
    const state = { q: params.get("q") || "", genero: params.get("genero") || "", marca: params.get("marca") || "", orden: "destacados" };
    const q = $("#q"), selMarca = $("#marca"), selOrden = $("#orden"), seg = $("#seg"), grid = $("#grid");

    const generos = ["Caballero", "Dama", "Unisex"].filter((g) => productos.some((p) => p.genero === g));
    seg.innerHTML = [["", "Todos", productos.length], ...generos.map((g) => [g, g, productos.filter((p) => p.genero === g).length])]
        .map(([v, l, n]) => `<button role="tab" data-v="${v}" aria-selected="false">${l}<span class="n">${n}</span></button>`).join("");
    const marcas = [...new Set(productos.map((p) => p.marca))].sort((a, b) => a.localeCompare(b, "es"));
    selMarca.insertAdjacentHTML("beforeend", marcas.map((m) => `<option>${esc(m)}</option>`).join(""));
    if (!productos.some((p) => p.precio)) selOrden.querySelectorAll('[value^="precio"]').forEach((o) => o.remove());
    // Acepta ?genero=dama en minúsculas
    state.genero = generos.find((g) => norm(g) === norm(state.genero)) || "";
    state.marca = marcas.find((m) => norm(m) === norm(state.marca)) || "";
    q.value = state.q; selMarca.value = state.marca;

    function render() {
        const t = norm(state.q.trim());
        let lista = productos.filter((p) =>
            (!state.genero || p.genero === state.genero) &&
            (!state.marca || p.marca === state.marca) &&
            (!t || t.split(/\s+/).every((w) => norm(`${p.marca} ${p.nombre} ${p.familia} ${p.etiquetas.join(" ")} ${p.presentacion}`).includes(w))));
        const val = (p) => p.precio_oferta || p.precio || Infinity;
        const ordenes = {
            destacados: (a, b) => (b.disponible - a.disponible) || (b.destacado - a.destacado),
            marca: (a, b) => a.marca.localeCompare(b.marca, "es") || a.nombre.localeCompare(b.nombre, "es"),
            "precio-asc": (a, b) => val(a) - val(b),
            "precio-desc": (a, b) => (val(b) === Infinity ? -1 : val(b)) - (val(a) === Infinity ? -1 : val(a)),
        };
        lista = [...lista].sort(ordenes[state.orden]);
        seg.querySelectorAll("button").forEach((b) => b.setAttribute("aria-selected", String(b.dataset.v === state.genero)));
        $("#count").textContent = `${lista.length} ${lista.length === 1 ? "fragancia" : "fragancias"}`;
        $("#empty").hidden = lista.length > 0;
        grid.innerHTML = lista.map((p, i) => `
            <article class="card glass${p.disponible ? "" : " is-out"}" style="animation-delay:${Math.min(i, 12) * 30}ms">
                <button class="card-media" data-open="${p.id}" aria-label="Ver ${esc(titulo(p))}">${img(p)}${badgesHTML(p)}</button>
                <div class="card-body">
                    <p class="brand">${esc(p.marca)}</p>
                    <h3 class="name"><button data-open="${p.id}">${esc(p.nombre)}</button></h3>
                    <div class="chips">${chipsHTML(p)}</div>
                    <div class="card-foot">${precioHTML(p)}
                        <a class="btn-wa btn-wa--sm" href="${waProducto(p)}" target="_blank" rel="noopener" data-track="${p.id}">${icon}Pedir</a>
                    </div>
                </div>
            </article>`).join("");
        // Mantiene los filtros en la URL para poder compartir colecciones (ej. ?genero=dama)
        const u = new URLSearchParams(location.search);
        [["q", state.q.trim()], ["genero", state.genero && norm(state.genero)], ["marca", state.marca]].forEach(([k, v]) => v ? u.set(k, v) : u.delete(k));
        history.replaceState(null, "", `${location.pathname}${u.toString() ? `?${u}` : ""}`);
    }

    let tq;
    q.addEventListener("input", () => { clearTimeout(tq); tq = setTimeout(() => { state.q = q.value; render(); }, 120); });
    seg.addEventListener("click", (e) => { const b = e.target.closest("button"); if (b) { state.genero = b.dataset.v; render(); } });
    selMarca.addEventListener("change", () => { state.marca = selMarca.value; render(); });
    selOrden.addEventListener("change", () => { state.orden = selOrden.value; render(); });

    // ---- Hoja de detalle ----
    const sheet = $("#sheet");
    let actual = null;
    function abrir(id) {
        const p = productos.find((x) => x.id === id);
        if (!p) return;
        actual = p;
        const im = $("#sheetImg");
        im.src = p.imagen || ""; im.alt = titulo(p); im.hidden = !p.imagen;
        $("#sheetBrand").textContent = p.marca;
        $("#sheetTitle").textContent = p.nombre;
        $("#sheetChips").innerHTML = chipsHTML(p);
        $("#sheetPrice").outerHTML = precioHTML(p).replace('class="price', 'id="sheetPrice" class="price price--lg');
        $("#sheetDesc").textContent = p.descripcion;
        $("#sheetWa").href = waProducto(p);
        $("#sheetWa").lastChild.textContent = p.disponible ? "Pedir por WhatsApp" : "Avisarme cuando llegue";
        if (!sheet.open) { sheet.showModal(); sheet.focus(); }
        const u = new URLSearchParams(location.search); u.set("p", p.id);
        history.replaceState(null, "", `${location.pathname}?${u}`);
        document.title = `${titulo(p)} | ${cfg.tienda}`;
    }
    function cerrar() { sheet.close(); }
    sheet.addEventListener("close", () => {
        const u = new URLSearchParams(location.search); u.delete("p");
        history.replaceState(null, "", `${location.pathname}${u.toString() ? `?${u}` : ""}`);
        document.title = `${cfg.tienda} | ${cfg.titulo}`;
    });
    sheet.addEventListener("click", (e) => { if (e.target === sheet) cerrar(); });
    $("#sheetClose").addEventListener("click", cerrar);
    grid.addEventListener("click", (e) => { const b = e.target.closest("[data-open]"); if (b) abrir(b.dataset.open); });

    function toast(t) {
        const el = $("#toast"); el.textContent = t; el.hidden = false;
        clearTimeout(toast.t); toast.t = setTimeout(() => (el.hidden = true), 2200);
    }
    $("#sheetShare").addEventListener("click", async () => {
        if (!actual) return;
        const url = `${base}p/${actual.id}/`;
        try {
            if (navigator.share) await navigator.share({ title: titulo(actual), url });
            else { await navigator.clipboard.writeText(url); toast("Enlace copiado"); }
        } catch (_) { /* el usuario canceló */ }
    });

    // ---- Textos de configuración ----
    const check = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12.5l4.5 4.5L19 7.5"/></svg>';
    $("#heroEyebrow").textContent = cfg.tienda;
    $("#heroTitle").textContent = cfg.titulo;
    $("#heroSub").textContent = cfg.subtitulo;
    $("#trust").innerHTML = (cfg.confianza || []).map((t) => `<li>${check}${esc(t)}</li>`).join("");
    const general = wa("Hola, vi su catálogo y quiero información.");
    $("#waTop").href = general;
    $("#waCta").href = wa("Hola, busco un perfume que no vi en el catálogo:");
    $("#waEmpty").addEventListener("click", () => { $("#waEmpty").href = wa(`Hola, busco el perfume "${q.value.trim()}". ¿Lo tienen?`); });
    $("#waEmpty").href = general;
    [["#faqEnvios", cfg.envios], ["#faqPagos", cfg.pagos]].forEach(([s, t]) => { if (t) { $(s).hidden = false; $(`${s} p`).textContent = t; } });
    $("#footBrand").textContent = cfg.tienda;
    $("#year").textContent = new Date().getFullYear();
    if (cfg.instagram) $("#footLinks").innerHTML = `<a href="https://instagram.com/${esc(cfg.instagram.replace(/^@/, ""))}" target="_blank" rel="noopener">Instagram</a>`;

    render();
    if (params.get("p")) abrir(params.get("p"));
})();
