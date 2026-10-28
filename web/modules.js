"use strict";
/* Read-only capability pages. Never sends POST/PUT/DELETE or runs commands. */
(function () {
  const make = (tag, cls, value) => {
    const node = document.createElement(tag);
    if (cls) node.className = cls;
    if (value != null) node.textContent = String(value);
    return node;
  };
  function notice(box, message) { box.append(make("p", "module-note", message)); }
  function heading(box, title, subtitle) {
    const top = make("div", "module-heading");
    top.append(make("h2", "", title), make("small", "", subtitle));
    box.append(top);
  }
  function grid(box, cols, rows) {
    if (!rows.length) return notice(box, "Nenhum registro disponível nesta instância.");
    const scroll = make("div", "module-scroll");
    const table = make("table", "module-table");
    const thead = make("thead"); const tr = make("tr");
    cols.forEach(c => tr.append(make("th", "", c)));
    thead.append(tr); table.append(thead);
    const body = make("tbody");
    for (const row of rows.slice(0, 90)) {
      const item = make("tr");
      row.forEach(col => item.append(make("td", "", col == null || col === "" ? "—" : col)));
      body.append(item);
    }
    table.append(body); scroll.append(table); box.append(scroll);
  }
  function readonly(box) {
    notice(box, "Somente leitura. Instalação, exclusão, criação e alterações exigem autenticação administrativa e ainda não estão habilitadas.");
  }
  function showResult(box, title, description, result, columns, renderer) {
    heading(box, title, description);
    if (!result || !result.available) {
      notice(box, result && result.reason || "Este recurso ainda não está disponível na instância StorOS.");
      return;
    }
    grid(box, columns, (result.items || []).map(renderer));
    readonly(box);
  }
  window.renderModuleDetails = function (view, box, data) {
    const d = data && data.modules;
    if (!d) {
      heading(box, "Módulo StorOS", "Aguardando dados da instância");
      notice(box, "Leituras ainda não disponíveis.");
      return true;
    }
    if (view === "users") {
      showResult(box, "Contas locais", "Somente usuários que existem nesta instalação Linux", d.users,
        ["CONTA", "UID", "DIRETÓRIO", "LOGIN"],
        x => [x.name, x.uid, x.home, x.login_enabled ? "Habilitado no sistema" : "Sem login"]);
      return true;
    }
    if (["images", "docker-network", "volumes"].includes(view)) {
      const config = {
        images: ["Imagens Docker locais", "Imagens obtidas da API Docker local", "images",
          ["REPOSITÓRIO", "TAG", "TAMANHO", "ID"], x => [x.Repository, x.Tag, x.Size, x.ID]],
        "docker-network": ["Redes Docker locais", "Redes existentes no daemon Docker", "networks",
          ["NOME", "DRIVER", "ESCOPO"], x => [x.Name, x.Driver, x.Scope]],
        volumes: ["Volumes Docker locais", "Volumes presentes no Docker desta instância", "volumes",
          ["NOME", "DRIVER"], x => [x.Name, x.Driver]],
      }[view];
      showResult(box, config[0], config[1], d.docker && d.docker[config[2]], config[3], config[4]);
      return true;
    }
    if (view === "vm-networks") {
      showResult(box, "Redes da virtualização", "Redes conhecidas pelo libvirt local",
        d.vm_networks, ["REDE"], x => [x.name]);
      return true;
    }
    if (view === "installed") {
      const r = data.containers;
      showResult(box, "Containers em execução",
        "Instalações não podem ser inferidas somente a partir de containers ativos",
        r, ["NOME", "IMAGEM", "ESTADO"], x => [x.name, x.image, x.status]);
      return true;
    }
    if (view === "system" || view === "settings") {
      heading(box, "Sistema e serviços", "Dados reais desta instalação StorOS");
      const os = d.system || {};
      grid(box, ["CAMPO", "VALOR"], [["Distribuição", os.os], ["Kernel", os.kernel],
          ["Arquitetura", os.architecture],
          ...Object.entries(os.services || {}).map(([k, v]) => [k, v])]);
      readonly(box);
      return true;
    }
    if (view === "monitoring") {
      const sys = data.status || {};
      const cpu = data.overview && data.overview.cpu || {};
      heading(box, "Monitoramento local", "Amostras atuais, não são histórico persistente");
      grid(box, ["MÉTRICA", "LEITURA"], [
        ["CPU", cpu.percent == null ? null : cpu.percent + "%"],
        ["Processador", cpu.model],
        ["Uptime", sys.uptime_seconds == null ? null : sys.uptime_seconds + " segundos"],
        ["Memória total", sys.ram_total_bytes == null ? null : (sys.ram_total_bytes / (1024**3)).toFixed(1) + " GiB"],
        ["Memória disponível", sys.ram_available_bytes == null ? null : (sys.ram_available_bytes / (1024**3)).toFixed(1) + " GiB"]]);
      readonly(box);
      return true;
    }
    const missing = {
      isos: ["Biblioteca ISO", "Catálogo e upload de ISOs ainda não integrados"],
      templates: ["Templates de VMs", "Biblioteca de templates de máquinas virtuais ainda não integrada"],
      logs: ["Logs Docker", "Acesso a logs restrito até existir controle de permissões e auditoria"],
      updates: ["Atualizações", "Atualização do sistema ainda não implementada"],
      notifications: ["Notificações", "Regras e histórico de alertas ainda não implementados"],
      tasks: ["Tarefas", "Fila de execução e histórico persistente ainda não implementados"],
      backup: ["Backup", "Rotinas de backup e restauração ainda não implementadas"],
      terminal: ["Terminal", "Terminal remoto desabilitado por segurança"],
    };
    if (missing[view]) {
      heading(box, missing[view][0], "Status real do módulo");
      notice(box, missing[view][1]);
      notice(box, "Não há registros simulados nem botões administrativos ativos.");
      return true;
    }
    return false;
  };
})();
