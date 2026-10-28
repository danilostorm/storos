"use strict";
/* Unraid-style XML Container v2 importer. Runs entirely in browser, no uploads.
   Generates a Compose JSON preview only; never creates containers or mounts. */
(function () {
  const file = document.getElementById("ca-template-file");
  const notice = document.getElementById("ca-template-status");
  if (!file || !notice) return;

  function direct(root, tag) {
    return Array.from(root.children).find(x => x.tagName === tag)?.textContent?.trim() || "";
  }
  function error(message) {
    notice.textContent = message;
    notice.className = "store-notice store-notice-error";
  }
  function parse(xml) {
    if (xml.length > 128000) throw Error("Arquivo XML maior que 128 KB");
    if (/<!DOCTYPE|<!ENTITY|<!\[CDATA/i.test(xml)) throw Error("DTD, entidades e CDATA não permitidos");
    const documentXML = new DOMParser().parseFromString(xml, "application/xml");
    if (documentXML.querySelector("parsererror")) throw Error("XML inválido");
    const root = documentXML.documentElement;
    if (root.tagName !== "Container" || root.getAttribute("version") !== "2")
      throw Error("É necessário um template Container XML v2");
    const name = direct(root, "Name");
    const image = direct(root, "Repository");
    if (!name || !/^[a-zA-Z0-9][A-Za-z0-9._/@:-]{0,200}$/.test(image))
      throw Error("Nome e Repository Docker válidos são obrigatórios");
    const slug = name.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "")
      .replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "").slice(0, 45);
    if (!slug) throw Error("Nome de serviço inválido");
    const issues = [];
    const network = direct(root, "Network").toLowerCase();
    if (network && network !== "bridge") issues.push("Rede diferente de bridge requer revisão manual");
    if (/^(true|yes|1)$/i.test(direct(root, "Privileged"))) issues.push("Modo privilegiado rejeitado");
    if (direct(root, "ExtraParams") || direct(root, "PostArgs"))
      issues.push("Parâmetros/comandos adicionais não importados");
    const ports = [];
    const volumes = {};
    const mounts = [];
    const env = {};
    const used = new Set();
    const configs = Array.from(root.children).filter(x => x.tagName === "Config");
    if (configs.length > 48) throw Error("Número excessivo de campos");
    configs.forEach((field, i) => {
      const kind = field.getAttribute("Type") || "";
      const target = field.getAttribute("Target") || "";
      const value = field.getAttribute("Default") || field.getAttribute("Value") || "";
      if (kind === "Port") {
        const inside = Number(target), outside = Number(value);
        if (!Number.isInteger(inside) || !Number.isInteger(outside) ||
            inside < 1 || inside > 65535 || outside < 1 || outside > 65535 || used.has(outside)) {
          issues.push("Porta inválida ou duplicada");
        } else {
          ports.push(String(outside) + ":" + String(inside));
          used.add(outside);
        }
      } else if (kind === "Path") {
        if (!target.startsWith("/") || target === "/" || target.includes("..") ||
            target.includes("//") || target === "/var/run/docker.sock" || mounts.some(x => x.endsWith(":" + target))) {
          issues.push("Montagem não permitida: " + target.slice(0, 70));
        } else {
          const volume = "storos_" + slug.replace(/-/g, "_") + "_" + i;
          volumes[volume] = {};
          mounts.push(volume + ":" + target);
        }
      } else if (kind === "Variable") {
        if (!/^[a-zA-Z_][a-zA-Z0-9_]{0,80}$/.test(target)) {
          issues.push("Variável inválida");
        } else if (/PASS|TOKEN|SECRET|KEY/i.test(target)) {
          issues.push("Variável confidencial " + target + " precisa ser informada");
          env[target] = "";
        } else {
          env[target] = String(value).slice(0, 500);
        }
      } else {
        issues.push("Campo não importado: " + String(kind).slice(0, 32));
      }
    });
    const service = {image, restart: "unless-stopped"};
    if (ports.length) service.ports = ports;
    if (mounts.length) service.volumes = mounts;
    if (Object.keys(env).length) service.environment = env;
    const compose = {name: "storos-" + slug, services: {[slug]: service}};
    if (Object.keys(volumes).length) compose.volumes = volumes;
    return {name, compose, issues};
  }

  file.addEventListener("change", async () => {
    try {
      const selection = file.files && file.files[0];
      if (!selection) return;
      if (selection.size > 128000) throw Error("Arquivo XML maior que 128 KB");
      const xml = await selection.text();
      const result = parse(xml);
      document.getElementById("compose-title").textContent = "Template XML — " + result.name;
      document.getElementById("compose-preview").value = JSON.stringify(result.compose, null, 2) + "\n";
      document.getElementById("compose-helper").textContent =
        "Prévia local, sem instalar. Volumes do host foram substituídos por volumes Docker nomeados.";
      notice.textContent = result.issues.length ?
        "Revisão obrigatória: " + result.issues.join("; ") :
        "Template lido no navegador. Prévia pronta; nenhuma instalação foi realizada.";
      notice.className = result.issues.length ? "store-notice store-notice-error" : "store-notice";
    } catch (e) {
      error("Não foi possível importar: " + e.message);
    } finally {
      file.value = "";
    }
  });
})();
