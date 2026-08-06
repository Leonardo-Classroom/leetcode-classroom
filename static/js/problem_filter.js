(function () {
  const form = document.getElementById("filter-form");
  const resultsEl = document.getElementById("problem-results");
  const clearLink = document.getElementById("clear-filters");
  if (!form || !resultsEl) return;

  const baseUrl = window.location.pathname;

  function fetchAndSwap(url, pushState) {
    fetch(url, { headers: { "X-Requested-With": "XMLHttpRequest" } })
      .then(function (r) { return r.text(); })
      .then(function (html) {
        resultsEl.innerHTML = html;
        bindPaginationLinks();
      });
    if (pushState) {
      history.pushState(null, "", url);
    }
  }

  function applyFilters() {
    const params = new URLSearchParams(new FormData(form));
    fetchAndSwap(baseUrl + "?" + params.toString(), true);
  }

  function bindPaginationLinks() {
    resultsEl.querySelectorAll("a.page-link").forEach(function (a) {
      a.addEventListener("click", function (e) {
        e.preventDefault();
        fetchAndSwap(this.getAttribute("href"), true);
        window.scrollTo({ top: 0, behavior: "smooth" });
      });
    });
  }

  function syncFormFromParams(params) {
    form.querySelectorAll('input[type="checkbox"]').forEach(function (el) {
      el.checked = params.getAll(el.name).includes(el.value);
    });
    const searchInput = form.querySelector('input[name="q"]');
    if (searchInput) searchInput.value = params.get("q") || "";
  }

  form.addEventListener("submit", function (e) {
    e.preventDefault();
    applyFilters();
  });

  form.querySelectorAll('input[type="checkbox"]').forEach(function (el) {
    el.addEventListener("change", applyFilters);
  });

  let debounceTimer;
  const searchInput = form.querySelector('input[name="q"]');
  if (searchInput) {
    searchInput.addEventListener("input", function () {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(applyFilters, 350);
    });
  }

  if (clearLink) {
    clearLink.addEventListener("click", function (e) {
      e.preventDefault();
      form.reset();
      form.querySelectorAll('input[type="checkbox"]').forEach(function (el) { el.checked = false; });
      fetchAndSwap(baseUrl, true);
    });
  }

  window.addEventListener("popstate", function () {
    const params = new URLSearchParams(window.location.search);
    syncFormFromParams(params);
    fetchAndSwap(window.location.pathname + window.location.search, false);
  });

  bindPaginationLinks();
})();
