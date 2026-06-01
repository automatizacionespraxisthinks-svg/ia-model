(function () {
  "use strict";

  const TOKEN_KEY = "praxis_admin_token";
  const USER_KEY = "praxis_admin_user";

  const token = localStorage.getItem(TOKEN_KEY);
  if (!token) {
    window.location.replace("/admin/login");
    return;
  }

  // ─── DOM refs ──────────────────────────────────────────────
  const currentUserEl = document.getElementById("current-user");
  const logoutBtn = document.getElementById("logout-btn");

  const createForm = document.getElementById("create-form");
  const keyNameInput = document.getElementById("key-name");
  const keyAdminInput = document.getElementById("key-admin");
  const createBtn = document.getElementById("create-btn");
  const createError = document.getElementById("create-error");

  const modal = document.getElementById("new-key-modal");
  const newKeyValue = document.getElementById("new-key-value");
  const copyKeyBtn = document.getElementById("copy-key-btn");
  const closeModalBtn = document.getElementById("close-modal-btn");

  const refreshBtn = document.getElementById("refresh-btn");
  const keysStatus = document.getElementById("keys-status");
  const keysTable = document.getElementById("keys-table");
  const keysTbody = document.getElementById("keys-tbody");

  const username = localStorage.getItem(USER_KEY) || "admin";
  currentUserEl.textContent = "👤 " + username;

  // ─── Helpers ───────────────────────────────────────────────
  function logout() {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    window.location.replace("/admin/login");
  }

  async function apiFetch(path, options = {}) {
    const headers = Object.assign(
      {
        "Content-Type": "application/json",
        Authorization: "Bearer " + token,
      },
      options.headers || {}
    );
    const res = await fetch(path, Object.assign({}, options, { headers }));
    if (res.status === 401 || res.status === 403) {
      logout();
      throw new Error("Sesión expirada");
    }
    return res;
  }

  function formatDate(iso) {
    if (!iso) return "—";
    const d = new Date(iso);
    if (isNaN(d.getTime())) return iso;
    return d.toLocaleString("es-ES", {
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    });
  }

  function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text == null ? "" : String(text);
    return div.innerHTML;
  }

  function showCreateError(msg) {
    createError.textContent = msg;
    createError.classList.remove("hidden");
  }

  function clearCreateError() {
    createError.textContent = "";
    createError.classList.add("hidden");
  }

  // ─── Listar keys ───────────────────────────────────────────
  async function loadKeys() {
    keysStatus.textContent = "Cargando...";
    keysStatus.classList.remove("hidden", "error");
    keysTable.classList.add("hidden");

    try {
      const res = await apiFetch("/v1/keys");
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || "Error al cargar keys");
      }
      const data = await res.json();
      renderKeys(data.keys || []);
      keysStatus.classList.add("hidden");
    } catch (err) {
      keysStatus.textContent = err.message || "Error al cargar keys";
      keysStatus.classList.add("error");
    }
  }

  function renderKeys(keys) {
    if (keys.length === 0) {
      keysStatus.textContent = "No hay keys creadas todavía.";
      keysStatus.classList.remove("hidden");
      keysTable.classList.add("hidden");
      return;
    }

    keysTbody.innerHTML = "";

    for (const k of keys) {
      const tr = document.createElement("tr");
      if (!k.is_active) tr.classList.add("row-inactive");

      tr.innerHTML = `
        <td>${escapeHtml(k.name)}</td>
        <td><code>${escapeHtml(k.key_prefix)}...</code></td>
        <td>${k.is_admin ? '<span class="badge badge-admin">admin</span>' : '<span class="badge">user</span>'}</td>
        <td>${k.is_active ? '<span class="badge badge-active">activa</span>' : '<span class="badge badge-inactive">revocada</span>'}</td>
        <td>${formatDate(k.created_at)}</td>
        <td>${formatDate(k.last_used_at)}</td>
        <td>${k.request_count.toLocaleString("es-ES")}</td>
        <td class="actions-cell"></td>
      `;

      const actionsCell = tr.querySelector(".actions-cell");
      if (k.is_active) {
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "btn-danger";
        btn.textContent = "Revocar";
        btn.addEventListener("click", () => revokeKey(k.id, k.name));
        actionsCell.appendChild(btn);
      }

      keysTbody.appendChild(tr);
    }

    keysTable.classList.remove("hidden");
  }

  async function revokeKey(id, name) {
    if (!confirm(`¿Revocar la key "${name}"? Esta acción no se puede deshacer.`)) {
      return;
    }
    try {
      const res = await apiFetch(`/v1/keys/${id}`, { method: "DELETE" });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || "Error al revocar");
      }
      await loadKeys();
    } catch (err) {
      alert(err.message || "Error al revocar la key");
    }
  }

  // ─── Crear key ─────────────────────────────────────────────
  createForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    clearCreateError();

    const name = keyNameInput.value.trim();
    const isAdmin = keyAdminInput.checked;

    if (!name) {
      showCreateError("El nombre es obligatorio.");
      return;
    }

    createBtn.disabled = true;
    createBtn.textContent = "Generando...";

    try {
      const res = await apiFetch("/v1/keys", {
        method: "POST",
        body: JSON.stringify({ name, is_admin: isAdmin }),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || "Error al crear la key");
      }
      const data = await res.json();
      showNewKeyModal(data.key);
      createForm.reset();
      await loadKeys();
    } catch (err) {
      showCreateError(err.message || "Error al crear la key");
    } finally {
      createBtn.disabled = false;
      createBtn.textContent = "Generar key";
    }
  });

  // ─── Modal nueva key ───────────────────────────────────────
  function showNewKeyModal(key) {
    newKeyValue.textContent = key;
    modal.classList.remove("hidden");
  }

  function hideModal() {
    modal.classList.add("hidden");
    newKeyValue.textContent = "";
  }

  closeModalBtn.addEventListener("click", hideModal);
  modal.addEventListener("click", (e) => {
    if (e.target === modal) hideModal();
  });

  copyKeyBtn.addEventListener("click", async () => {
    const text = newKeyValue.textContent;
    try {
      await navigator.clipboard.writeText(text);
      const original = copyKeyBtn.textContent;
      copyKeyBtn.textContent = "¡Copiada!";
      setTimeout(() => (copyKeyBtn.textContent = original), 1500);
    } catch (_) {
      // Fallback
      const range = document.createRange();
      range.selectNode(newKeyValue);
      window.getSelection().removeAllRanges();
      window.getSelection().addRange(range);
      alert("Selecciónala y copia manualmente (Ctrl+C).");
    }
  });

  // ─── Misc ──────────────────────────────────────────────────
  refreshBtn.addEventListener("click", loadKeys);
  logoutBtn.addEventListener("click", logout);

  loadKeys();
})();
