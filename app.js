const state = {
  products: [],
  query: "",
  color: "全部",
  cart: new Map(),
  currentPage: 1,
  activeSelectionId: null,
};

const MAX_PAGES = 5;
const UNIT_PRICE = 100;

const colorStyles = {
  紅: "#cf4c43",
  橘: "#df8540",
  黃: "#e0bc3f",
  綠: "#4f9867",
  藍: "#4777af",
  紫: "#875aa0",
  灰: "#8b8d88",
  白: "#f8f4e8",
  咖啡: "#8a6046",
};

const productPhotos = {
  P001: "assets/product-photos/P001-hong-10-zhuhong.jpg",
  P027: "assets/product-photos/P027-hong-12-mihongse.jpg",
  P028: "assets/product-photos/P028-hong-13-mihongse.jpg",
  P033: "assets/product-photos/P033-hong-13-shanhufen.jpg",
  P036: "assets/product-photos/P036-hong-10-lihongse.jpg",
  P038: "assets/product-photos/P038-hong-11-haitanghong.jpg",
  P049: "assets/product-photos/P049-hong-14-danfei.jpg",
  P054: "assets/product-photos/P054-hong-10-anhongmei.jpg",
  P055: "assets/product-photos/P055-hong-12-anhongmei.jpg",
  P057: "assets/product-photos/P057-hong-08-feihong.jpg",
  P058: "assets/product-photos/P058-hong-10-feihong.jpg",
  P087: "assets/product-photos/P087-huang-09-yuehuang.jpg",
  P088: "assets/product-photos/P088-huang-11-yuehuang.jpg",
  P089: "assets/product-photos/P089-huang-11-yuehuang.jpg",
  P090: "assets/product-photos/P090-huang-12-yuehuang.jpg",
  P096: "assets/product-photos/P096-huang-13-yuehuang.jpg",
  P097: "assets/product-photos/P097-huang-12-baihuang.jpg",
  P098: "assets/product-photos/P098-huang-14-baihuang.jpg",
  P102: "assets/product-photos/P102-huang-12-danyuehuang.jpg",
};

const els = {
  productCount: document.querySelector("#productCount"),
  selectedCount: document.querySelector("#selectedCount"),
  searchInput: document.querySelector("#searchInput"),
  colorFilters: document.querySelector("#colorFilters"),
  clearFilters: document.querySelector("#clearFilters"),
  productGrid: document.querySelector("#productGrid"),
  paginationTop: document.querySelector("#paginationTop"),
  paginationBottom: document.querySelector("#paginationBottom"),
  resultSummary: document.querySelector("#resultSummary"),
  cartSummary: document.querySelector("#cartSummary"),
  cartItems: document.querySelector("#cartItems"),
  clearCart: document.querySelector("#clearCart"),
  orderForm: document.querySelector("#orderForm"),
  orderDialog: document.querySelector("#orderDialog"),
  orderText: document.querySelector("#orderText"),
  copyOrder: document.querySelector("#copyOrder"),
  closeDialog: document.querySelector("#closeDialog"),
};

async function init() {
  const response = await fetch("data/pigments.json");
  state.products = await response.json();
  state.products.sort((a, b) => {
    const colorOrder = Object.keys(colorStyles);
    return Number(hasPhoto(b)) - Number(hasPhoto(a))
      || colorOrder.indexOf(a.color) - colorOrder.indexOf(b.color)
      || a.name.localeCompare(b.name, "zh-Hant")
      || a.code.localeCompare(b.code, "zh-Hant");
  });

  buildFilters();
  bindEvents();
  render();
}

function bindEvents() {
  els.searchInput.addEventListener("input", (event) => {
    state.query = event.target.value.trim().toLowerCase();
    state.currentPage = 1;
    renderProducts();
  });

  els.clearFilters.addEventListener("click", () => {
    state.query = "";
    state.color = "全部";
    state.currentPage = 1;
    els.searchInput.value = "";
    render();
  });

  els.clearCart.addEventListener("click", () => {
    state.cart.clear();
    state.activeSelectionId = null;
    render();
  });

  els.productGrid.addEventListener("click", (event) => {
    const button = event.target.closest("[data-action]");
    if (!button) return;

    const id = button.dataset.id;
    const qty = state.cart.get(id) || 0;
    if (button.dataset.action === "increase") {
      state.cart.set(id, qty + 1);
      state.activeSelectionId = id;
    }
    if (button.dataset.action === "decrease") {
      if (qty <= 1) state.cart.delete(id);
      else state.cart.set(id, qty - 1);
      state.activeSelectionId = state.cart.has(id) ? id : null;
    }
    render();
  });

  document.addEventListener("click", (event) => {
    const button = event.target.closest("[data-page]");
    if (!button) return;

    state.currentPage = Number(button.dataset.page);
    renderProducts();
    document.querySelector(".catalog-panel").scrollIntoView({ block: "start", behavior: "smooth" });
  });

  els.orderForm.addEventListener("submit", (event) => {
    event.preventDefault();
    if (state.cart.size === 0) {
      alert("請先選擇至少一款顏料");
      return;
    }
    const formData = new FormData(els.orderForm);
    els.orderText.value = buildOrderText(formData);
    els.orderDialog.showModal();
  });

  els.copyOrder.addEventListener("click", async () => {
    await navigator.clipboard.writeText(els.orderText.value);
    els.copyOrder.textContent = "已複製";
    window.setTimeout(() => {
      els.copyOrder.textContent = "複製文字";
    }, 1200);
  });
}

function buildFilters() {
  const counts = state.products.reduce((acc, product) => {
    acc[product.color] = (acc[product.color] || 0) + 1;
    return acc;
  }, {});
  const colors = ["全部", ...Object.keys(colorStyles).filter((color) => counts[color])];

  els.colorFilters.innerHTML = colors.map((color) => {
    const count = color === "全部" ? state.products.length : counts[color];
    const swatch = color === "全部"
      ? "linear-gradient(135deg, #cf4c43 0 22%, #e0bc3f 22% 44%, #4f9867 44% 66%, #4777af 66% 100%)"
      : colorStyles[color];
    return `
      <button class="color-pill" type="button" data-color="${color}">
        <span class="color-pill__label">
          <span class="color-dot" style="background:${swatch}"></span>
          ${color}
        </span>
        <span>${count}</span>
      </button>
    `;
  }).join("");

  els.colorFilters.addEventListener("click", (event) => {
    const button = event.target.closest("[data-color]");
    if (!button) return;
    state.color = button.dataset.color;
    state.currentPage = 1;
    render();
  });
}

function render() {
  els.productCount.textContent = `${state.products.length} 款顏料`;
  renderProducts();
  renderCart();
  renderFilterState();
}

function renderFilterState() {
  document.querySelectorAll(".color-pill").forEach((button) => {
    button.classList.toggle("active", button.dataset.color === state.color);
  });
}

function getFilteredProducts() {
  const filtered = state.products.filter((product) => {
    const matchesColor = state.color === "全部" || product.color === state.color;
    const haystack = `${product.name} ${product.code} ${product.color}`.toLowerCase();
    return matchesColor && haystack.includes(state.query);
  });

  return filtered.sort((a, b) => {
    const aPinned = isPinnedSelection(a);
    const bPinned = isPinnedSelection(b);
    return Number(bPinned) - Number(aPinned)
      || Number(hasPhoto(b)) - Number(hasPhoto(a))
      || productSort(a, b);
  });
}

function renderProducts() {
  const products = getFilteredProducts();
  const pageInfo = getPageInfo(products.length);
  const pageProducts = products.slice(pageInfo.start, pageInfo.end);
  const pinnedVisible = products.filter(isPinnedSelection).length;
  const selectedText = pinnedVisible ? `，已選品項置頂 ${pinnedVisible} 款` : "";
  els.resultSummary.textContent = products.length
    ? `顯示 ${products.length} 款，第 ${pageInfo.currentPage} / ${pageInfo.totalPages} 頁${selectedText}`
    : "找不到符合條件的顏料";
  els.productGrid.innerHTML = pageProducts.length
    ? pageProducts.map(productCard).join("")
    : `<div class="empty-state">找不到符合條件的顏料</div>`;
  renderPagination(pageInfo);
  renderFilterState();
}

function getPageInfo(totalItems) {
  if (totalItems === 0) {
    state.currentPage = 1;
    return { currentPage: 1, totalPages: 1, start: 0, end: 0 };
  }

  const pageSize = Math.max(1, Math.ceil(state.products.length / MAX_PAGES));
  const totalPages = Math.max(1, Math.ceil(totalItems / pageSize));
  state.currentPage = Math.min(Math.max(1, state.currentPage), totalPages);
  const start = (state.currentPage - 1) * pageSize;
  return {
    currentPage: state.currentPage,
    totalPages,
    start,
    end: start + pageSize,
  };
}

function renderPagination({ currentPage, totalPages }) {
  const controls = totalPages <= 1
    ? ""
    : Array.from({ length: totalPages }, (_, index) => {
      const page = index + 1;
      const active = page === currentPage ? " active" : "";
      return `<button class="page-button${active}" type="button" data-page="${page}">${page}</button>`;
    }).join("");
  const html = controls
    ? `<span>頁面</span>${controls}`
    : "";
  els.paginationTop.innerHTML = html;
  els.paginationBottom.innerHTML = html;
}

function productCard(product) {
  const qty = state.cart.get(product.id) || 0;
  const selected = qty > 0 ? " selected" : "";
  const swatch = colorStyles[product.color] || "#ddd";
  const photo = productPhotos[product.id];
  const visual = photo
    ? `<img class="product-photo" src="${photo}" alt="${escapeHtml(product.name)} 色號 ${escapeHtml(product.code)}">`
    : `<span class="swatch" style="background:${swatch}"></span>`;
  return `
    <article class="product-card${selected}">
      <div class="swatch-row">
        ${visual}
        <span class="code-tag">${photo ? "實拍" : "色系"} / 色號 ${escapeHtml(product.code)}</span>
      </div>
      <div>
        <div class="product-name">${escapeHtml(product.name)}</div>
        <div class="product-meta">${escapeHtml(product.color)}色系</div>
        <div class="product-price">每包 $${UNIT_PRICE}</div>
      </div>
      <div class="stepper" aria-label="${escapeHtml(product.name)} 數量">
        <button type="button" data-action="decrease" data-id="${product.id}" aria-label="減少">−</button>
        <output>${qty}</output>
        <button type="button" data-action="increase" data-id="${product.id}" aria-label="增加">+</button>
      </div>
    </article>
  `;
}

function renderCart() {
  const items = getCartItems();
  const totals = getOrderTotals(items);
  const totalQty = totals.paidQty;
  els.selectedCount.textContent = `已選 ${totalQty} 件`;
  els.cartSummary.textContent = items.length
    ? `${items.length} 款顏料，共 ${totals.paidQty} 包，合計 $${totals.totalPrice}`
    : "尚未選擇顏料";

  if (!items.length) {
    els.cartItems.className = "cart-items empty";
    els.cartItems.textContent = "選好顏料後會顯示在這裡";
    return;
  }

  els.cartItems.className = "cart-items";
  els.cartItems.innerHTML = `
    <div class="cart-total">
      <span>共 ${totals.paidQty} 包</span>
      <strong>$${totals.totalPrice}</strong>
    </div>
    ${items.map(({ product, qty }) => `
    <div class="cart-item">
      <div>
        <strong>${escapeHtml(product.name)}</strong>
        <small>${escapeHtml(product.color)}色系 / 色號 ${escapeHtml(product.code)}</small>
      </div>
      <div class="cart-qty">${qty}</div>
    </div>
  `).join("")}
  `;
}

function getCartItems() {
  return Array.from(state.cart.entries())
    .map(([id, qty]) => ({
      product: state.products.find((item) => item.id === id),
      qty,
    }))
    .filter((item) => item.product);
}

function getOrderTotals(items = getCartItems()) {
  const paidQty = items.reduce((sum, item) => sum + item.qty, 0);
  return {
    paidQty,
    totalPrice: paidQty * UNIT_PRICE,
  };
}

function buildOrderText(formData) {
  const now = new Date();
  const orderId = `IH${now.getFullYear()}${String(now.getMonth() + 1).padStart(2, "0")}${String(now.getDate()).padStart(2, "0")}-${String(now.getHours()).padStart(2, "0")}${String(now.getMinutes()).padStart(2, "0")}`;
  const items = getCartItems();
  const totals = getOrderTotals(items);
  const lines = items.map(({ product, qty }, index) => {
    return `${index + 1}. ${product.name}（${product.color} / 色號 ${product.code}） x ${qty} 包`;
  });

  return [
    "稻花香顏料訂單",
    `訂單編號：${orderId}`,
    "",
    "商品：",
    ...lines,
    "",
    `單價：每包 $${UNIT_PRICE}`,
    `總包數：${totals.paidQty} 包`,
    `應付金額：$${totals.totalPrice}`,
    "",
    `收件人：${formData.get("recipient")}`,
    `電話：${formData.get("phone")}`,
    `地址：${formData.get("address")}`,
    `備註：${formData.get("note") || "無"}`,
  ].join("\n");
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function hasPhoto(product) {
  return Boolean(productPhotos[product.id]);
}

function isPinnedSelection(product) {
  return state.cart.has(product.id) && product.id !== state.activeSelectionId;
}

function productSort(a, b) {
  const colorOrder = Object.keys(colorStyles);
  return colorOrder.indexOf(a.color) - colorOrder.indexOf(b.color)
    || a.name.localeCompare(b.name, "zh-Hant")
    || a.code.localeCompare(b.code, "zh-Hant");
}

init().catch((error) => {
  console.error(error);
  els.resultSummary.textContent = "顏料資料載入失敗";
});
