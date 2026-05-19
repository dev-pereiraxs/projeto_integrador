(function () {
  function ready(fn) {
    if (document.readyState === "loading")
      document.addEventListener("DOMContentLoaded", fn);
    else fn();
  }

  ready(function () {
    // Theme toggle
    const themeBtn = document.getElementById("afThemeToggle");
    if (themeBtn) {
      const savedTheme = localStorage.getItem("afTheme") || "dark";
      if (savedTheme === "light")
        document.documentElement.classList.add("light-mode");

      updateThemeIcon();

      themeBtn.addEventListener("click", () => {
        document.documentElement.classList.toggle("light-mode");
        const isDark =
          !document.documentElement.classList.contains("light-mode");
        localStorage.setItem("afTheme", isDark ? "dark" : "light");
        updateThemeIcon();
      });
    }

    function updateThemeIcon() {
      if (!themeBtn) return;
      const isDark = !document.documentElement.classList.contains("light-mode");
      themeBtn.textContent = isDark ? "🌙" : "☀️";
    }

    // Mobile menu
    const burger = document.getElementById("afHamburger");
    const mobile = document.getElementById("afMobileMenu");
    if (!burger || !mobile) return;

    burger.addEventListener("click", () => {
      const isOpen = mobile.classList.contains("open");
      mobile.classList.toggle("open", !isOpen);
      burger.setAttribute("aria-expanded", !isOpen ? "true" : "false");
    });

    mobile.querySelectorAll("a").forEach((a) => {
      a.addEventListener("click", () => {
        mobile.classList.remove("open");
        burger.setAttribute("aria-expanded", "false");
      });
    });

    document.addEventListener("click", (e) => {
      if (!mobile.classList.contains("open")) return;
      if (!mobile.contains(e.target) && !burger.contains(e.target)) {
        mobile.classList.remove("open");
        burger.setAttribute("aria-expanded", "false");
      }
    });

    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && mobile.classList.contains("open")) {
        mobile.classList.remove("open");
        burger.setAttribute("aria-expanded", "false");
      }
    });
  });
})();
