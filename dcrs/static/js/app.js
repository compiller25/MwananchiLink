/* Lodrick DCRS — App JS */

(function () {
  // ── Theme ──────────────────────────────────────────────────────────────
  const THEME_KEY = "dcrs_theme";

  function getTheme() {
    return localStorage.getItem(THEME_KEY) ||
      (window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
  }

  function applyTheme(theme) {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem(THEME_KEY, theme);
    document.querySelectorAll("[data-theme-toggle]").forEach(btn => {
      const icon = btn.querySelector("i");
      const label = btn.querySelector(".theme-label");
      if (icon) {
        icon.className = theme === "dark" ? "bi bi-sun" : "bi bi-moon";
      }
      if (label) {
        label.textContent = theme === "dark" ? "Light" : "Dark";
      }
      btn.setAttribute("title", theme === "dark" ? "Switch to light mode" : "Switch to dark mode");
    });
  }

  // Apply theme before paint (no flash)
  applyTheme(getTheme());

  document.addEventListener("DOMContentLoaded", () => {
    // Re-apply to sync icons
    applyTheme(getTheme());

    // Theme toggle buttons
    document.querySelectorAll("[data-theme-toggle]").forEach(btn => {
      btn.addEventListener("click", () => {
        const next = document.documentElement.getAttribute("data-theme") === "dark" ? "light" : "dark";
        applyTheme(next);
      });
    });

    // ── Sidebar ─────────────────────────────────────────────────────────
    const shell    = document.getElementById("appShell");
    const overlay  = document.getElementById("sidebarOverlay");
    const hamburger = document.querySelector("[data-sidebar-toggle]");

    function openSidebar() {
      shell.classList.add("sidebar-open");
      if (overlay) overlay.classList.add("visible");
    }
    function closeSidebar() {
      shell.classList.remove("sidebar-open");
      if (overlay) overlay.classList.remove("visible");
    }

    if (hamburger) hamburger.addEventListener("click", () => {
      shell.classList.contains("sidebar-open") ? closeSidebar() : openSidebar();
    });

    if (overlay) overlay.addEventListener("click", closeSidebar);

    // ── Active sidebar link ──────────────────────────────────────────────
    const currentPath = window.location.pathname;
    document.querySelectorAll(".sidebar-link").forEach(link => {
      const href = link.getAttribute("href");
      if (href && href !== "/" && currentPath.startsWith(href)) {
        link.classList.add("active");
      }
    });

    // ── Auto-dismiss alerts ──────────────────────────────────────────────
    document.querySelectorAll(".alert[data-autodismiss]").forEach(el => {
      setTimeout(() => {
        el.style.opacity = "0";
        el.style.transition = "opacity 0.4s";
        setTimeout(() => el.remove(), 400);
      }, 4000);
    });

    // ── Show / hide password ─────────────────────────────────────────────
    document.querySelectorAll('input[type="password"]').forEach(input => {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "pw-toggle";
      btn.setAttribute("aria-label", "Toggle password visibility");
      btn.setAttribute("aria-pressed", "false");
      btn.innerHTML = '<i class="bi bi-eye"></i>';

      const wrap = input.closest(".input-icon-wrap");
      if (wrap) {
        wrap.classList.add("pw-field");
        wrap.appendChild(btn);
      } else {
        const pos = document.createElement("span");
        pos.className = "pw-field";
        pos.style.cssText = "position:relative;display:block";
        input.parentNode.insertBefore(pos, input);
        pos.appendChild(input);
        pos.appendChild(btn);
      }

      btn.addEventListener("click", () => {
        const show = input.type === "password";
        input.type = show ? "text" : "password";
        btn.innerHTML = show ? '<i class="bi bi-eye-slash"></i>' : '<i class="bi bi-eye"></i>';
        btn.setAttribute("aria-pressed", show ? "true" : "false");
        input.focus();
      });
    });

    // ── Multi-step registration wizard ───────────────────────────────────
    const regForm = document.getElementById("regForm");
    if (regForm) {
      const steps = regForm.querySelectorAll(".reg-step");
      const rp = regForm.querySelectorAll(".rp-step");
      let cur = 0;

      function showStep(i) {
        steps.forEach((s, idx) => { s.hidden = idx !== i; });
        rp.forEach((p, idx) => {
          p.classList.toggle("active", idx === i);
          p.classList.toggle("done", idx < i);
        });
        cur = i;
        window.scrollTo({ top: 0, behavior: "smooth" });
        const first = steps[i].querySelector("input, select, textarea");
        if (first) first.focus();
      }

      regForm.querySelectorAll("[data-next]").forEach(btn => {
        btn.addEventListener("click", () => {
          const fields = steps[cur].querySelectorAll("input, select, textarea");
          let ok = true;
          fields.forEach(f => { if (!f.disabled && !f.reportValidity()) ok = false; });
          if (ok && cur < steps.length - 1) showStep(cur + 1);
        });
      });

      regForm.querySelectorAll("[data-back]").forEach(btn => {
        btn.addEventListener("click", () => { if (cur > 0) showStep(cur - 1); });
      });

      showStep(0);
    }
  });
})();
