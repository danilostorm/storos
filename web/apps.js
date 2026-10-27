"use strict";
// The Store is strictly discovery/preview in this release. No privileged browser operations.
const storEl = id => document.getElementById(id);
const storNode = (tag, klass, value) => {
  const x = document.createElement(tag);
  if (klass) x.className = klass;
  if (value != null) x.textContent = String(value);
  return x;
};
async function storGet(path) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 10000);
  try {
    const response = await fetch(path, {signal: controller.signal, cache: "no-store"});
    const body = await response.json();
    if (!response.ok) throw new Error(body.error || "HTTP " + response.status);
    return body;
  } finally { clearTimeout(timer); }
}
function showNotice(target, message, isError = false) {
  target.textContent = message;
  target.className = isError ? "store-notice store-notice-error" : "store-notice";
}
async function loadEngine() {
  const target = storEl("engine-info");
  try {
    const m = await storGet("/api/apps/engine");
    showNotice(target, "Docker " + (m.docker_installed ? "instalado" : "não instalado") +
      " · Compose " + (m.compose_installed ? "disponível" : "indisponível") +
      " · Daemon " + (m.daemon_active ? "ativo" : "parado") +
      " · Instalação no painel desabilitada nesta versão");
  } catch (e) { showNotice(target, "Motor Docker indisponível: " + e.message, true); }
}
async function previewCompose(slug, name) {
  const target = storEl("compose-preview");
  const title = storEl("compose-title");
  title.textContent = "Compose — " + name;
  try {
    const d = await storGet("/api/apps/compose?slug=" + encodeURIComponent(slug));
    target.value = d.compose;
    storEl("compose-helper").textContent = d.warning;
    target.focus();
  } catch (e) { showNotice(storEl("compose-helper"), "Falha na prévia: " + e.message, true); }
}
async function loadCatalog() {
  const target = storEl("catalog-list");
  try {
    const data = await storGet("/api/apps/catalog");
    target.replaceChildren();
    for (const item of data.items) {
      const card = storNode("article", "market-card");
      card.append(storNode("div", "market-symbol", item.name.substring(0, 1)));
      const title = storNode("h3", "", item.name);
      const tag = storNode("span", "market-tag", item.category);
      const desc = storNode("p", "", item.description);
      const image = storNode("code", "market-image", item.image);
      const actions = storNode("div", "market-actions");
      const button = storNode("button", "store-action", "Ver Docker Compose");
      button.type = "button";
      button.addEventListener("click", () => previewCompose(item.slug, item.name));
      actions.append(button);
      card.append(tag, title, desc, image, actions);
      target.append(card);
    }
  } catch (e) { showNotice(target, "Catálogo indisponível: " + e.message, true); }
}
async function searchHub(event) {
  event.preventDefault();
  const term = storEl("hub-query").value.trim();
  const target = storEl("hub-results");
  if (term.length < 2 || term.length > 45) {
    showNotice(target, "Digite de 2 a 45 caracteres.", true);
    return;
  }
  showNotice(target, "Consultando Docker Hub...");
  try {
    const data = await storGet("/api/apps/hub?q=" + encodeURIComponent(term));
    target.replaceChildren();
    if (!data.items.length) return showNotice(target, "Nenhuma imagem encontrada.");
    for (const image of data.items) {
      const line = storNode("article", "hub-item");
      const text = storNode("div", "");
      text.append(storNode("strong", "", image.name));
      text.append(storNode("p", "", image.description || "Sem descrição"));
      const a = storNode("a", "hub-link", image.official ? "Oficial · Docker Hub" : "Ver no Docker Hub");
      a.href = image.url;
      a.target = "_blank";
      a.rel = "noopener noreferrer";
      line.append(text, a);
      target.append(line);
    }
  } catch (e) { showNotice(target, e.message, true); }
}
const billingKeys = [
  ["cpu_watts", "CPU configurada (W)", 0], ["board_watts", "Placa-mãe e ventoinhas (W)", 0],
  ["ram_watts", "Memória total (W)", 0], ["threads", "Threads do host", 1],
  ["host_ram_gib", "RAM total do host (GiB)", 1], ["vcpus", "vCPU da VM/container", 0],
  ["ram_gib", "RAM reservada (GiB)", 0], ["gpu_watts", "GPU dedicada em passthrough (W)", 0],
  ["hours", "Horas ativas no ciclo", 0], ["electricity_kwh", "Energia (R$/kWh)", 0],
  ["uptime_hour", "Hora ativa (R$/h)", 0], ["plan_price", "Preço do plano de internet (R$)", 0],
  ["total_cycle_gb", "Tráfego total do plano (GB)", 0], ["item_cycle_gb", "Tráfego deste serviço (GB)", 0]
];
function money(n) {
  return Number(n).toLocaleString("pt-BR", {style: "currency", currency: "BRL"});
}
function buildBillingFields() {
  const target = storEl("billing-fields");
  for (const [key, title, min] of billingKeys) {
    const field = storNode("label", "billing-field");
    const titleNode = storNode("span", "", title);
    const input = storNode("input");
    input.id = "billing-" + key;
    input.name = key;
    input.type = "number";
    input.required = true;
    input.min = String(min);
    input.step = "any";
    input.value = "0";
    field.append(titleNode, input);
    target.append(field);
  }
}
async function loadBillingDefaults() {
  try {
    const model = await storGet("/api/billing/model");
    storEl("billing-threads").value = model.threads;
    storEl("billing-host_ram_gib").value = model.host_ram_gib;
    showNotice(storEl("billing-state"), "Modelo pronto. Defina sua potência, tarifas e horas reais; todos os valores são estimativas.");
  } catch (e) { showNotice(storEl("billing-state"), e.message, true); }
}
function towerExample() {
  const sample = {
    cpu_watts: 135, board_watts: 95, ram_watts: 24, threads: 40,
    host_ram_gib: 128, vcpus: 4, ram_gib: 8, gpu_watts: 0,
    hours: 240, electricity_kwh: 1, uptime_hour: 0,
    plan_price: 60, total_cycle_gb: 100, item_cycle_gb: 25
  };
  for (const [key, value] of Object.entries(sample)) storEl("billing-" + key).value = value;
  showNotice(storEl("billing-state"), "Exemplo do modelo Tower carregado. Não representa o consumo real do seu equipamento.");
}
async function estimateCosts(event) {
  event.preventDefault();
  const args = new URLSearchParams();
  for (const [key] of billingKeys) {
    const node = storEl("billing-" + key);
    if (!node.checkValidity()) return node.reportValidity();
    args.set(key, node.value);
  }
  try {
    const d = await storGet("/api/billing/estimate?" + args.toString());
    storEl("billing-total").textContent = money(d.cost_total);
    storEl("billing-energy-cost").textContent = money(d.cost_energy);
    storEl("billing-internet-cost").textContent = money(d.cost_internet);
    storEl("billing-uptime-cost").textContent = money(d.cost_uptime);
    storEl("billing-power").textContent = d.watts_total.toLocaleString("pt-BR") + " W alocados · " +
      d.kwh.toLocaleString("pt-BR") + " kWh estimados";
    showNotice(storEl("billing-state"), "Estimativa calculada pelo módulo de custos adaptado do Tower Command Center.");
  } catch (e) { showNotice(storEl("billing-state"), "Falha: " + e.message, true); }
}
buildBillingFields();
loadEngine();
loadCatalog();
loadBillingDefaults();
storEl("hub-form").addEventListener("submit", searchHub);
storEl("billing-form").addEventListener("submit", estimateCosts);
storEl("billing-example").addEventListener("click", towerExample);
storEl("compose-copy").addEventListener("click", async () => {
  const text = storEl("compose-preview").value;
  if (!text) return;
  try { await navigator.clipboard.writeText(text); showNotice(storEl("compose-helper"), "Compose copiado! Revise antes de executar."); }
  catch (_) { storEl("compose-preview").select(); showNotice(storEl("compose-helper"), "Selecione e copie o texto manualmente."); }
});
