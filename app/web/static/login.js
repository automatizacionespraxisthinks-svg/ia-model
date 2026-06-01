(function () {
  "use strict";

  // Si ya hay token, salta directo al dashboard
  if (localStorage.getItem("praxis_admin_token")) {
    window.location.replace("/admin/");
    return;
  }

  const form = document.getElementById("login-form");
  const usernameInput = document.getElementById("username");
  const passwordInput = document.getElementById("password");
  const submitBtn = document.getElementById("submit-btn");
  const errorMsg = document.getElementById("error-msg");

  function showError(text) {
    errorMsg.textContent = text;
    errorMsg.classList.remove("hidden");
  }

  function clearError() {
    errorMsg.textContent = "";
    errorMsg.classList.add("hidden");
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    clearError();

    const username = usernameInput.value.trim();
    const password = passwordInput.value;

    if (!username || !password) {
      showError("Ingresa usuario y contraseña.");
      return;
    }

    submitBtn.disabled = true;
    submitBtn.textContent = "Verificando...";

    try {
      const res = await fetch("/admin/api/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });

      if (!res.ok) {
        let detail = "Credenciales inválidas.";
        try {
          const data = await res.json();
          if (data && data.detail) detail = data.detail;
        } catch (_) {}
        throw new Error(detail);
      }

      const data = await res.json();
      if (!data || !data.token) {
        throw new Error("Respuesta inválida del servidor.");
      }

      localStorage.setItem("praxis_admin_token", data.token);
      localStorage.setItem("praxis_admin_user", username);
      window.location.replace("/admin/");
    } catch (err) {
      showError(err.message || "Error al iniciar sesión.");
      submitBtn.disabled = false;
      submitBtn.textContent = "Ingresar";
      passwordInput.focus();
      passwordInput.select();
    }
  });
})();
