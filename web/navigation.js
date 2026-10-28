"use strict";
/* StorOS navigation and readability controls. No server calls or privileged actions. */
(() => {
  const body = document.body;
  const sidebar = document.querySelector(".sidebar");
  const topbar = document.querySelector(".topbar");
  const brand = document.querySelector(".brand");
  if (!sidebar || !topbar || !brand) return;

  const read = (key, fallback) => {
    try { return localStorage.getItem(key) || fallback; } catch (_) { return fallback; }
  };
  const save = (key, value) => {
    try { localStorage.setItem(key, value); } catch (_) {}
  };
  const mobile = () => window.matchMedia("(max-width: 720px)").matches;
  const menuButton = document.createElement("button");
  menuButton.type = "button";
  menuButton.id = "sidebar-toggle";
  menuButton.className = "sidebar-toggle";
  menuButton.setAttribute("aria-label", "Recolher menu lateral");
  menuButton.setAttribute("aria-controls", "storos-side-menu");
  menuButton.setAttribute("aria-expanded", "true");
  menuButton.title = "Recolher menu";
  menuButton.innerHTML = '<svg aria-hidden="true" viewBox="0 0 24 24"><path d="M4 4h16v16H4zM10 4v16M6.5 9h1M6.5 13h1"/></svg>';
  topbar.insertBefore(menuButton, topbar.firstChild);

  const fontButton = document.createElement("button");
  fontButton.type = "button";
  fontButton.id = "font-size-toggle";
  fontButton.className = "icon-button font-size-toggle";
  fontButton.setAttribute("aria-label", "Aumentar tamanho do texto");
  fontButton.setAttribute("aria-live", "polite");
  fontButton.title = "Ampliar textos";
  fontButton.textContent = "A+";
  const actions = topbar.querySelector(".top-actions");
  if (actions) actions.insertBefore(fontButton, actions.firstChild);

  sidebar.id = "storos-side-menu";
  const shade = document.createElement("button");
  shade.type = "button";
  shade.className = "sidebar-backdrop";
  shade.id = "sidebar-backdrop";
  shade.setAttribute("aria-label", "Fechar menu");
  shade.hidden = true;
  sidebar.after(shade);

  for (const link of sidebar.querySelectorAll(".side-menu a[data-target]")) {
    for (const child of [...link.childNodes]) {
      if (child.nodeType === 3 && child.textContent.trim()) {
        const span = document.createElement("span");
        span.className = "nav-label";
        span.textContent = child.textContent.trim();
        link.replaceChild(span, child);
      }
    }
    const label = link.querySelector(".nav-label");
    if (label) {
      link.title = label.textContent;
      if (!link.getAttribute("aria-label")) link.setAttribute("aria-label", label.textContent);
    }
  }

  for (const [index, group] of [...sidebar.querySelectorAll(".nav-parent")].entries()) {
    const subnav = group.querySelector(".subnav");
    const link = group.querySelector(":scope > .nav-link");
    if (!subnav || !link) continue;
    const sectionName = link.querySelector(".nav-label")?.textContent || "seção";
    const key = "storos-section-" + (link.dataset.target || index);
    const id = "submenu-" + index;
    subnav.id = id;
    const toggle = document.createElement("button");
    toggle.type = "button";
    toggle.className = "submenu-toggle";
    toggle.title = "Recolher " + sectionName;
    toggle.setAttribute("aria-label", "Recolher " + sectionName);
    toggle.setAttribute("aria-controls", id);
    toggle.textContent = "⌄";
    const setGroup = (open) => {
      group.classList.toggle("section-closed", !open);
      toggle.setAttribute("aria-expanded", String(open));
      toggle.title = (open ? "Recolher " : "Expandir ") + sectionName;
      toggle.setAttribute("aria-label", toggle.title);
      save(key, open ? "open" : "closed");
    };
    setGroup(read(key, "open") !== "closed");
    toggle.addEventListener("click", () => setGroup(group.classList.contains("section-closed")));
    group.append(toggle);
  }

  let compact = read("storos-sidebar-mode", "expanded") === "compact";
  let fontSize = Number(read("storos-text-size", "0"));
  fontSize = Number.isInteger(fontSize) && fontSize >= 0 && fontSize <= 2 ? fontSize : 0;

  const applySidebar = () => {
    if (mobile()) {
      body.classList.remove("sidebar-collapsed");
    } else {
      body.classList.toggle("sidebar-collapsed", compact);
      body.classList.remove("sidebar-open");
    }
    const expanded = mobile() ? body.classList.contains("sidebar-open") : !compact;
    menuButton.setAttribute("aria-expanded", String(expanded));
    menuButton.setAttribute("aria-label",
      mobile() ? (expanded ? "Fechar menu" : "Abrir menu") :
      (compact ? "Expandir menu lateral" : "Recolher menu lateral"));
    menuButton.title = menuButton.getAttribute("aria-label");
    shade.hidden = !mobile() || !expanded;
    body.classList.toggle("nav-dialog-open", mobile() && expanded);
  };
  const closeMobile = () => {
    if (body.classList.contains("sidebar-open")) {
      body.classList.remove("sidebar-open");
      applySidebar();
      menuButton.focus();
    }
  };
  menuButton.addEventListener("click", () => {
    if (mobile()) body.classList.toggle("sidebar-open");
    else { compact = !compact; save("storos-sidebar-mode", compact ? "compact" : "expanded"); }
    applySidebar();
  });
  shade.addEventListener("click", closeMobile);
  document.addEventListener("keydown", ev => {
    if (ev.key === "Escape" && mobile()) closeMobile();
  });
  sidebar.addEventListener("click", ev => {
    if (mobile() && ev.target.closest("a[data-target]")) closeMobile();
  });
  window.addEventListener("resize", applySidebar);

  const applyFontSize = () => {
    body.dataset.textSize = String(fontSize);
    fontButton.textContent = fontSize === 0 ? "A+" : fontSize === 1 ? "A++" : "A";
    fontButton.title = fontSize === 2 ? "Voltar ao tamanho normal" : "Ampliar textos";
    fontButton.setAttribute("aria-label", fontButton.title);
  };
  fontButton.addEventListener("click", () => {
    fontSize = (fontSize + 1) % 3;
    save("storos-text-size", String(fontSize));
    applyFontSize();
  });
  applyFontSize();
  applySidebar();
})();
