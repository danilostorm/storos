"use strict";
/* Optional login UI. Browser never receives the session token: HttpOnly cookie.
   Only an explicit --auth-socket on the LAN gateway activates this form. */
(function () {
  const node = (tag, cls, text) => {
    const x = document.createElement(tag);
    if (cls) x.className = cls;
    if (text != null) x.textContent = text;
    return x;
  };
  const api = async (url, options) => {
    const response = await fetch(url, Object.assign({
      credentials: "same-origin", cache: "no-store",
    }, options || {}));
    const value = await response.json();
    if (!response.ok) throw new Error(value.error || "Autenticação indisponível");
    return value;
  };
  window.renderNativeLogin = async function (target) {
    const panel = node("section", "native-auth-panel");
    panel.append(node("h3", "", "Login nativo do StorOS"));
    const status = node("p", "", "Verificando serviço de autenticação...");
    panel.append(status);
    target.append(panel);
    try {
      const available = await api("/api/native/status");
      if (!panel.isConnected) return;
      if (!available.enabled) {
        status.textContent = "Não habilitado neste laboratório. O painel continua protegido pelo acesso HTTPS existente.";
        return;
      }
      status.textContent = "Serviço de identidade privada disponível. Não concede permissões de gerenciamento de discos ou Docker.";
      const form = node("form", "native-auth-form");
      const user = node("input");
      user.type = "text";
      user.autocomplete = "username";
      user.placeholder = "Usuário StorOS";
      user.required = true;
      user.minLength = 3;
      user.maxLength = 32;
      const password = node("input");
      password.type = "password";
      password.autocomplete = "current-password";
      password.placeholder = "Senha";
      password.required = true;
      const login = node("button", "store-action", "Entrar");
      login.type = "submit";
      const logout = node("button", "outline-button", "Encerrar sessão");
      logout.type = "button";
      logout.hidden = true;
      const feedback = node("p", "native-auth-feedback");
      form.append(user, password, login, logout);
      panel.append(form, feedback);
      async function loadSession() {
        try {
          const who = await api("/api/native/me");
          feedback.textContent = "Sessão nativa: " + who.name + " (" + who.role + ")";
          logout.hidden = false;
        } catch (_) {
          feedback.textContent = "Nenhuma sessão nativa autenticada nesta aba.";
          logout.hidden = true;
        }
      }
      await loadSession();
      form.addEventListener("submit", async ev => {
        ev.preventDefault();
        login.disabled = true;
        feedback.textContent = "Autenticando...";
        try {
          const result = await api("/api/native/login", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({username: user.value, password: password.value}),
          });
          password.value = "";
          sessionStorage.setItem("storos_native_csrf", result.csrf_token);
          await loadSession();
        } catch (e) {
          password.value = "";
          feedback.textContent = e.message;
        } finally {
          login.disabled = false;
        }
      });
      logout.addEventListener("click", async () => {
        const csrf = sessionStorage.getItem("storos_native_csrf");
        if (!csrf) {
          feedback.textContent = "Para encerrar a sessão, autentique-se novamente nesta aba.";
          return;
        }
        try {
          await api("/api/native/logout", {
            method: "POST", headers: {"X-StorOS-CSRF": csrf}, body: "",
          });
          sessionStorage.removeItem("storos_native_csrf");
          await loadSession();
        } catch (e) {
          feedback.textContent = e.message;
        }
      });
    } catch (_) {
      if (panel.isConnected) status.textContent = "Não foi possível consultar a autenticação nativa.";
    }
  };
})();
