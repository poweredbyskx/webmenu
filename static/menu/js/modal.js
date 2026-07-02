document.addEventListener("DOMContentLoaded", function () {
  const modalOverlay = document.getElementById("product-modal-overlay");
  if (!modalOverlay) return;

  const modalImage = document.getElementById("product-modal-image");
  const modalTitle = document.getElementById("product-modal-title");
  const modalPrice = document.getElementById("product-modal-price");
  const modalDescription = document.getElementById("product-modal-description");
  const modalCloseButton = document.getElementById("product-modal-close");

  window.openProductModal = function (itemEl) {
    const name = itemEl.dataset.name || "";
    const price = itemEl.dataset.price || "";
    const description = itemEl.dataset.description || "";
    const imageUrl = itemEl.dataset.image || "";
    const category = itemEl.dataset.category || "";

    modalTitle.textContent = name;
    modalPrice.textContent = price;
    modalDescription.textContent = description;

    if (imageUrl) {
      modalImage.src = imageUrl;
      modalImage.alt = name;
      modalImage.style.display = "block";
    } else {
      modalImage.removeAttribute("src");
      modalImage.alt = "";
      modalImage.style.display = "none";
    }

    const isDrink = ['non_coffee', 'ice_coffee', 'cocktails'].includes(category);
    const productCard = modalOverlay.querySelector('.product-card');
    if (productCard) productCard.classList.toggle('product-card--drink', isDrink);

    modalOverlay.classList.add("open");
    modalOverlay.setAttribute("aria-hidden", "false");
    document.body.style.overflow = "hidden";
    track('item_view', {item: name, category: category});
  };

  window.closeProductModal = function () {
    modalOverlay.classList.remove("open");
    modalOverlay.setAttribute("aria-hidden", "true");
    document.body.style.overflow = "";
  };

  if (modalCloseButton) {
    modalCloseButton.addEventListener("click", window.closeProductModal);
  }
  modalOverlay.addEventListener("click", function (e) {
    if (e.target === modalOverlay) window.closeProductModal();
  });
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && modalOverlay.classList.contains("open")) window.closeProductModal();
  });
});
