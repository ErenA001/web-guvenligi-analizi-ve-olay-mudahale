(() => {
  const nativeFetch = window.fetch.bind(window);
  let redirecting = false;

  function redirectToLogin() {
    if (redirecting || window.location.pathname.startsWith("/login")) return;
    redirecting = true;
    const next = `${window.location.pathname}${window.location.search}${window.location.hash}`;
    window.location.assign(`/login?next=${encodeURIComponent(next || "/")}`);
  }

  window.fetch = async (...args) => {
    const response = await nativeFetch(...args);
    if (response.status === 401) redirectToLogin();
    return response;
  };

  function installSessionControls(username) {
    const actionBar = document.querySelector(".topbar-actions");
    if (!actionBar || actionBar.querySelector(".logout-button")) return false;

    const userSession = document.createElement("div");
    userSession.className = "user-session";
    userSession.title = "Aktif kullanıcı";

    const avatar = document.createElement("span");
    avatar.textContent = (username || "U").slice(0, 1).toUpperCase();
    const label = document.createElement("strong");
    label.textContent = username || "kullanıcı";
    userSession.append(avatar, label);

    const logoutButton = document.createElement("button");
    logoutButton.className = "logout-button";
    logoutButton.type = "button";
    logoutButton.textContent = "Çıkış";
    logoutButton.setAttribute("aria-label", "Oturumu kapat");
    logoutButton.title = "Çıkış yap";
    logoutButton.addEventListener("click", async () => {
      logoutButton.disabled = true;
      try {
        await nativeFetch("/logout", {
          method: "POST",
          credentials: "same-origin",
          headers: { "X-Requested-With": "SecureAI" },
        });
      } finally {
        window.location.assign("/login");
      }
    });

    const refreshButton = actionBar.querySelector(".refresh-button");
    actionBar.insertBefore(userSession, refreshButton || null);
    actionBar.appendChild(logoutButton);
    return true;
  }

  async function initializeSessionControls() {
    try {
      const response = await nativeFetch("/api/dashboard", {
        credentials: "same-origin",
        headers: { Accept: "application/json" },
      });
      if (response.status === 401) {
        redirectToLogin();
        return;
      }
      if (!response.ok) return;

      const payload = await response.json();
      if (installSessionControls(payload.username)) return;

      const observer = new MutationObserver(() => {
        if (installSessionControls(payload.username)) observer.disconnect();
      });
      observer.observe(document.documentElement, { childList: true, subtree: true });
      window.setTimeout(() => observer.disconnect(), 10000);
    } catch (_error) {
      // The main dashboard already displays its own connection error state.
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initializeSessionControls, { once: true });
  } else {
    initializeSessionControls();
  }
})();
