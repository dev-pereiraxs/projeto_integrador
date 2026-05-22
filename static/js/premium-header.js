(function () {
  function ready(fn) {
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", fn);
    } else {
      fn();
    }
  }

  ready(function () {
    const burger = document.getElementById("afHamburger");
    const mobile = document.getElementById("afMobileMenu");

    if (!burger || !mobile) return;

    function close() {
      mobile.classList.remove("open");
      mobile.setAttribute("aria-hidden", "true");
      burger.setAttribute("aria-expanded", "false");
    }

    function open() {
      mobile.classList.add("open");
      mobile.setAttribute("aria-hidden", "false");
      burger.setAttribute("aria-expanded", "true");
    }

    burger.addEventListener("click", () => {
      mobile.classList.contains("open") ? close() : open();
    });

    mobile.querySelectorAll("a").forEach((a) => a.addEventListener("click", close));

    document.addEventListener("click", (e) => {
      if (!mobile.classList.contains("open")) return;
      if (!mobile.contains(e.target) && !burger.contains(e.target)) close();
    });

    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape") close();
    });
  });
})();

