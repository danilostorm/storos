"use strict";
/* Read-only, data-driven StorOS storage detail pages. Inserts API values only through safe textContent. */
(function () {
  const el = (tag, cls, value) => {
    const out = document.createElement(tag);
    if (cls) out.className = cls;
    if (value !== null && value !== undefined) out.textContent = String(value);
    return out;
  };
  const human = (v) => {
    if (v == null || !Number.isFinite(Number(v)) || Number(v) < 0) return "—";
    const n = Number(v);
    if (n === 0) return "0 B";
    const units = ["B", "KiB", "MiB", "GiB", "TiB", "PiB"];
    const i = Math.min(5, Math.floor(Math.log(n) / Math.log(1024)));
    return (n / 1024 ** i).toFixed(i ? 1 : 0) + " " + units[i];
  };
  function addKV(parent, title, value) {
    const wrap = el("div", "storage-kv");
    wrap.append(el("small", "", title), el("strong", "", value == null || value === "" ? "—" : value));
    parent.append(wrap);
  }
  function table(cols, rows) {
    const scroll = el("div", "storage-scroll");
    const tab = el("table", "storage-table");
    const head = el("thead");
    const hr = el("tr");
    cols.forEach(col => hr.append(el("th", "", col)));
    head.append(hr);
    const body = el("tbody");
    if (!rows.length) {
      const r = el("tr");
      const c = el("td", "storage-empty", "Nenhum registro encontrado");
      c.colSpan = cols.length;
      r.append(c);
      body.append(r);
    } else {
      rows.forEach(row => {
        const r = el("tr");
        row.forEach(value => r.append(el("td", "", value == null || value === "" ? "—" : value)));
        body.append(r);
      });
    }
    tab.append(head, body);
    scroll.append(tab);
    return scroll;
  }
  function notification(parent, message) {
    parent.append(el("p", "storage-info", message));
  }
  window.renderStorageDetails = function (container, report) {
    container.replaceChildren();
    if (!report) return notification(container, "Aguardando inventário real da instância StorOS.");
    const notice = el("div", "storage-notice");
    notice.append(el("strong", "", "Inventário somente leitura"),
      el("span", "", report.scope || "Sistema StorOS local"));
    container.append(notice);
    if (!report.available) return notification(container, report.reason || "Acesso ao inventário indisponível.");
    const disks = Array.isArray(report.disks) ? report.disks : [];
    const summary = el("div", "storage-summary");
    addKV(summary, "Dispositivos detectados", disks.length);
    addKV(summary, "Partições/volumes detectados", disks.reduce((n, d) => n + (d.partitions || []).length, 0));
    addKV(summary, "Administração de discos", "Desativada nesta prévia");
    container.append(summary);
    const sections = report.sections || {};
    const byName = Object.fromEntries(disks.map(d => [d.name, d]));
    for (const [id, title] of [
      ["array", "Dispositivos do Array"],
      ["pools", "Dispositivos dos Pools"],
      ["boot", "Dispositivo de Boot"],
      ["other", "Outros Dispositivos Detectados"]
    ]) {
      const group = sections[id] || {configured:false,items:[],reason:"Classificação indisponível"};
      const section = el("section", "storage-group");
      const top = el("div", "storage-group-top");
      top.append(el("h2", "", title),
        el("span", "storage-group-state", group.configured ? (group.items || []).length + " dispositivo(s)" : "Não configurado"));
      section.append(top);
      const names = (group.items || []).filter(n => byName[n]);
      if (names.length) {
        section.append(table(["DISPOSITIVO", "IDENTIFICAÇÃO", "CAPACIDADE", "LEITURA", "GRAVAÇÃO", "ERROS", "SISTEMA", "USO", "SMART"], names.map(n => {
          const disk = byName[n];
          const fs = [...new Set((disk.partitions || []).map(p => p.filesystem).filter(Boolean))].join(", ");
          const measured = (disk.partitions || []).find(p => p.usage && p.usage.percent != null);
          return [disk.name, disk.model || disk.transport || null, human(disk.size_bytes),
                  disk.io && disk.io.reads_bps != null ? human(disk.io.reads_bps) + "/s" : null,
                  disk.io && disk.io.writes_bps != null ? human(disk.io.writes_bps) + "/s" : null,
                  disk.io && disk.io.errors != null ? disk.io.errors : null,
                  fs || null, measured ? measured.usage.percent + "%" : null,
                  disk.smart && disk.smart.available ? disk.smart.health : null];
        })));
      } else {
        notification(section, group.reason || (id === "boot" ? "Dispositivo de inicialização não identificado" : "Nenhum dispositivo configurado"));
      }
      container.append(section);
    }
    const actions = el("section", "storage-group");
    const actionTitle = el("div", "storage-group-top");
    actionTitle.append(el("h2", "", "Operações do Array"), el("span", "storage-group-state", "Desativadas"));
    actions.append(actionTitle);
    notification(actions, "Start, Stop, Check, Spin Up/Down, Move, Reboot e Shutdown serão habilitados apenas após autenticação administrativa, array real e testes de segurança.");
    container.append(actions);
    if (!disks.length) return notification(container, "Nenhum dispositivo de bloco detectado nesta instância.");
    container.append(el("h2", "storage-partitions-title", "Detalhes de Discos e Partições"));
    for (const disk of disks) {
      const card = el("section", "storage-disk");
      const header = el("div", "storage-disk-header");
      const heading = el("div", "storage-disk-heading");
      heading.append(el("h2", "", disk.name || "Disco sem identificação"),
        el("span", "", disk.model || (disk.transport === "virtio" ? "Disco virtual VirtIO" : "Modelo não informado")));
      const size = el("span", "storage-size", human(disk.size_bytes));
      header.append(heading, size);
      card.append(header);
      const info = el("div", "storage-meta");
      addKV(info, "Conexão", disk.transport ? String(disk.transport).toUpperCase() : "Não informada");
      addKV(info, "Modo do dispositivo", disk.read_only ? "Somente leitura" : "Gravação possível no sistema");
      const smart = disk.smart || {};
      addKV(info, "SMART", smart.available ? (smart.health || "Sem resultado") : "Indisponível");
      card.append(info);
      if (!smart.available && smart.reason) {
        card.append(el("p", "storage-hint", smart.reason));
      } else if (smart.health === "FAILED") {
        card.append(el("p", "storage-health-warning", "SMART informou falha. Faça backup e consulte diagnóstico especializado."));
      }
      const rows = (disk.partitions || []).map(p => [
        p.name, human(p.size_bytes), p.filesystem, p.label,
        (p.mountpoints || []).join(", ") || "Não montado",
        p.usage && p.usage.percent != null ?
          p.usage.percent + "% (" + human(p.usage.used_bytes) + " de " + human(p.usage.total_bytes) + ")" : null,
      ]);
      card.append(table(["PARTIÇÃO", "CAPACIDADE", "FORMATO", "RÓTULO", "MONTAGEM", "ESPAÇO UTILIZADO"], rows));
      container.append(card);
    }
    notification(container, "Esta tela não formata discos, cria pools, altera partições ou modifica montagens.");
  };
  window.renderSharesDetails = function (container, report) {
    container.replaceChildren();
    const scope = el("div", "storage-notice");
    scope.append(el("strong", "", "Compartilhamentos locais — somente leitura"),
      el("span", "", "Configurações SMB e NFS visíveis dentro desta instância StorOS, não do Unraid hospedeiro."));
    container.append(scope);
    if (!report) return notification(container, "Aguardando coleta de compartilhamentos.");
    for (const [protocol, label] of [["smb", "Compartilhamentos SMB / Samba"], ["nfs", "Exportações NFS"]]) {
      const block = el("section", "storage-disk");
      block.append(el("h2", "storage-section-heading", label));
      const data = report.shares && report.shares[protocol];
      if (!data || !data.available) {
        notification(block, data && data.reason || "Configuração não disponível para leitura.");
      } else if (!(data.items || []).length) {
        notification(block, "Nenhum compartilhamento configurado nesta instância.");
      } else if (protocol === "smb") {
        block.append(table(["NOME", "CAMINHO", "SOMENTE LEITURA"], data.items.map(x => [x.name, x.path, x.read_only])));
      } else {
        block.append(table(["CAMINHO EXPORTADO", "REGRAS DE CLIENTES"], data.items.map(x => [x.path, x.clients_configured == null ? null : String(x.clients_configured)])));
      }
      container.append(block);
    }
    notification(container, "Criar, excluir e alterar permissões de compartilhamentos ainda exige um módulo administrativo autenticado.");
  };
})();
