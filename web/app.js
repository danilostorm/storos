"use strict";
const el = id => document.getElementById(id);
function formatBytes(value) {
  if (!Number.isFinite(Number(value)) || Number(value) < 0) return "—";
  const n = Number(value);
  if (n === 0) return "0 B";
  const units = ["B", "KiB", "MiB", "GiB", "TiB", "PiB"];
  const idx = Math.min(5, Math.max(0, Math.floor(Math.log(n) / Math.log(1024))));
  return (n / (1024 ** idx)).toFixed(idx ? 1 : 0) + " " + units[idx];
}
function showText(id, value) { el(id).textContent = value == null ? "—" : String(value); }
async function request(endpoint) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 5000);
  try {
    const response = await fetch(endpoint, {signal: controller.signal, cache: "no-store"});
    if (!response.ok) throw new Error(endpoint + ": HTTP " + response.status);
    return await response.json();
  } finally { clearTimeout(timer); }
}
function element(tag, cls, value) {
  const node = document.createElement(tag);
  if (cls) node.className = cls;
  if (value !== undefined) node.textContent = String(value);
  return node;
}
function unavailable(target, reason) {
  target.replaceChildren(element("div", "placeholder", reason || "Indisponível neste ambiente"));
}
function renderSystem(status) {
  showText("host", status.host);
  showText("host-os", status.os);
  const total = Number(status.ram_total_bytes) || 0;
  const available = Number(status.ram_available_bytes) || 0;
  const used = Math.max(0, total - available);
  const percentage = total ? Math.round(used / total * 100) : 0;
  showText("memory", total ? percentage + "%" : "—");
  el("memory-bar").style.width = percentage + "%";
  showText("memory-sub", formatBytes(used) + " / " + formatBytes(total) + " em uso");
  const up = status.uptime_seconds;
  showText("uptime", Number.isFinite(up) ? "Uptime " + Math.floor(up / 86400) + " dias" : "Uptime indisponível");
}
function renderDisks(result) {
  const target = el("disk-list");
  const disks = Array.isArray(result.devices) ? result.devices.filter(d => d.type === "disk" && !/^zram/.test(d.name || "")) : [];
  showText("disk-count", disks.length + " discos");
  if (!result.available) return unavailable(target, result.reason);
  if (!disks.length) return unavailable(target, "Nenhum dispositivo visível.");
  target.replaceChildren();
  for (const d of disks) {
    const row = element("div", "table-row");
    row.append(element("span", "dev-name", d.name || "—"));
    row.append(element("span", "", formatBytes(d.size)));
    const fs = d.fstype || (Array.isArray(d.children) && d.children.length ? d.children.map(c => c.fstype).filter(Boolean).join(", ") : "") || "—";
    row.append(element("span", "fs", fs));
    target.append(row);
  }
}
function renderEntities(result, targetId, countId) {
  const target = el(targetId);
  const items = Array.isArray(result.items) ? result.items : [];
  showText(countId, items.length);
  if (!result.available) return unavailable(target, result.reason);
  if (!items.length) return unavailable(target, "Nenhum item encontrado.");
  target.replaceChildren();
  for (const item of items) {
    const row = element("div", "entity");
    row.append(element("span", "entity-name", item.name));
    row.append(element("span", "entity-status", item.status || "Identificada"));
    target.append(row);
  }
}
function renderApps(result) {
  const target = el("apps-list");
  const items = Array.isArray(result.items) ? result.items : [];
  showText("container-count", items.length);
  showText("apps-count", items.length + " ativos");
  showText("container-sub", result.available ? "Containers em execução" : "Integração indisponível");
  if (!result.available) return unavailable(target, result.reason);
  if (!items.length) return unavailable(target, "Nenhum container ativo.");
  target.replaceChildren();
  for (const app of items) {
    const tile = element("div", "app-tile");
    tile.append(element("span", "app-symbol", (app.name || "A").substring(0, 1).toUpperCase()));
    const info = element("div", "app-info");
    info.append(element("div", "app-title", app.name));
    info.append(element("div", "app-status", app.status || "Em execução"));
    tile.append(info);
    target.append(tile);
  }
}
async function refresh() {
  const button = el("reload");
  button.disabled = true;
  el("error").hidden = true;
  const endpoints = ["/api/status", "/api/disks", "/api/vms", "/api/containers"];
  try {
    const outcomes = await Promise.allSettled(endpoints.map(request));
    if (outcomes[0].status === "fulfilled") renderSystem(outcomes[0].value);
    if (outcomes[1].status === "fulfilled") renderDisks(outcomes[1].value);
    if (outcomes[2].status === "fulfilled") {
      renderEntities(outcomes[2].value, "vm-list", "compute-count");
      showText("vm-count", (outcomes[2].value.items || []).length);
      showText("vm-sub", "Máquinas virtuais identificadas");
    }
    if (outcomes[3].status === "fulfilled") renderApps(outcomes[3].value);
    const failures = outcomes.filter(o => o.status === "rejected");
    if (failures.length) {
      el("error").textContent = "Não foi possível consultar " + failures.length + " módulo(s). Verifique a API local do StorOS.";
      el("error").hidden = false;
    }
    showText("checked-time", "Atualizado " + new Date().toLocaleTimeString("pt-BR"));
  } catch (error) {
    el("error").textContent = "O painel não conseguiu atualizar: " + error.message;
    el("error").hidden = false;
  } finally { button.disabled = false; }
}
el("reload").addEventListener("click", refresh);
refresh();
