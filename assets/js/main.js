/* LA Associates — minimal progressive enhancement (no dependencies) */
(function () {
  "use strict";

  // Nav menu. The links live behind the toggle at every screen size, so the
  // menu is the only way to navigate — it needs to be dismissible the ways
  // people expect: the button, choosing a link, Escape, or clicking away.
  var toggle = document.querySelector(".nav__toggle");
  var links = document.getElementById("nav-links");
  if (toggle && links) {
    var setOpen = function (open) {
      links.classList.toggle("is-open", open);
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
    };
    var isOpen = function () {
      return links.classList.contains("is-open");
    };

    toggle.addEventListener("click", function () {
      setOpen(!isOpen());
    });

    // Close after choosing a link
    links.addEventListener("click", function (e) {
      if (e.target.tagName === "A") setOpen(false);
    });

    // Escape closes and returns focus to the button
    document.addEventListener("keydown", function (e) {
      if ((e.key === "Escape" || e.key === "Esc") && isOpen()) {
        setOpen(false);
        toggle.focus();
      }
    });

    // Clicking anywhere outside closes
    document.addEventListener("click", function (e) {
      if (!isOpen()) return;
      if (links.contains(e.target) || toggle.contains(e.target)) return;
      setOpen(false);
    });
  }

  // Auto-update the copyright year
  var year = document.getElementById("year");
  if (year) {
    year.textContent = new Date().getFullYear();
  }
})();
