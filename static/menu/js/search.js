document.addEventListener("DOMContentLoaded", function () {
  const container = document.querySelector(".search-container");
  const input = document.querySelector(".search-input");
  const results = document.querySelector(".search-results");

  if (!container || !input || !results) return;

  const searchUrl = container.dataset.searchUrl;
  const menuUrl = container.dataset.menuUrl;
  const trackSource = container.dataset.trackSource || "";
  let timer = null;

  function escapeHtml(text) {
    return String(text)
      .replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;").replaceAll("'", "&#039;");
  }

  input.addEventListener("input", function () {
    const q = input.value.trim();
    clearTimeout(timer);
    if (!q) { results.innerHTML = ""; results.style.display = "none"; return; }
    timer = setTimeout(async function () {
      try {
        const response = await fetch(`${searchUrl}?q=${encodeURIComponent(q)}`);
        const data = await response.json();
        if (!Array.isArray(data) || data.length === 0) {
          results.innerHTML = `<div class="search-item">Ничего не найдено</div>`;
          results.style.display = "flex";
          return;
        }
        track('search_used', {query: q, results_count: data.length});
        results.innerHTML = data.map(item => `
          <a class="search-item"
             href="${menuUrl}?category=${encodeURIComponent(item.category_slug)}&item=${encodeURIComponent(item.item_slug)}"
             data-track-item="${escapeHtml(item.name)}" data-track-category="${escapeHtml(item.category || '')}">
            ${item.image ? `<img src="${item.image}" alt="${escapeHtml(item.name)}" style="width:44px;height:44px;object-fit:cover;border-radius:8px;">` : ""}
            <div style="display:flex;flex-direction:column;">
              <strong style="font-size:13px;color:#652a29;">${escapeHtml(item.name)}</strong>
              <span style="font-size:12px;color:#652a29;">${escapeHtml(item.price)} · ${escapeHtml(item.category || "")}</span>
            </div>
          </a>
        `).join("");
        results.style.display = "flex";
        results.querySelectorAll('a[data-track-item]').forEach(function (el) {
          el.addEventListener('click', function () {
            track('search_result_click', {item: el.dataset.trackItem, category: el.dataset.trackCategory, source: trackSource});
          }, {once: true});
        });
      } catch (error) {
        results.innerHTML = `<div class="search-item">Ошибка поиска</div>`;
        results.style.display = "flex";
      }
    }, 250);
  });

  document.addEventListener("click", function (e) {
    if (!e.target.closest(".search-container")) results.style.display = "none";
  });
  input.addEventListener("focus", function () {
    if (results.innerHTML.trim()) results.style.display = "flex";
  });
});
