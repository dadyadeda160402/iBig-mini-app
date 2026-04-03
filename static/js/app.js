"use strict";

/* ─────────────────────── Telegram WebApp init ─────────────────────────── */
const tg = window.Telegram && window.Telegram.WebApp ? window.Telegram.WebApp : null;

if (tg) {
  tg.ready();
  tg.expand();

  // Светлая тема
  if (tg.colorScheme === "light") {
    document.documentElement.setAttribute("data-theme", "light");
  }

  // Прокидываем CSS-переменные Telegram
  const root = document.documentElement;
  const tp = tg.themeParams || {};
  const cssMap = {
    "--tg-theme-bg-color":            tp.bg_color,
    "--tg-theme-text-color":          tp.text_color,
    "--tg-theme-hint-color":          tp.hint_color,
    "--tg-theme-button-color":        tp.button_color,
    "--tg-theme-button-text-color":   tp.button_text_color,
    "--tg-theme-secondary-bg-color":  tp.secondary_bg_color,
  };
  for (const [prop, val] of Object.entries(cssMap)) {
    if (val) root.style.setProperty(prop, val);
  }

  // Имя пользователя
  try {
    const u = tg.initDataUnsafe && tg.initDataUnsafe.user;
    if (u) {
      const name = [u.first_name, u.last_name].filter(Boolean).join(" ") || "@" + (u.username || "");
      const el = document.getElementById("tgUserLine");
      if (el) el.textContent = name;
    }
  } catch (_) {}
}

/* ─────────────────────── Навигация по вкладкам ────────────────────────── */
document.querySelectorAll(".nav button").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".nav button").forEach((b) => b.classList.remove("active"));
    document.querySelectorAll(".tab").forEach((t) => (t.style.display = "none"));
    btn.classList.add("active");
    const tab = document.getElementById("tab-" + btn.dataset.tab);
    if (tab) tab.style.display = "";
  });
});

/* ─────────────────────── Модели устройств ─────────────────────────────── */
const DEVICE_MODELS = {
  "Смартфон": [
    "iPhone 16 Pro Max", "iPhone 16 Pro", "iPhone 16 Plus", "iPhone 16",
    "iPhone 15 Pro Max", "iPhone 15 Pro", "iPhone 15 Plus", "iPhone 15",
    "iPhone 14 Pro Max", "iPhone 14 Pro", "iPhone 14 Plus", "iPhone 14",
    "iPhone 13 Pro Max", "iPhone 13 Pro", "iPhone 13", "iPhone 13 mini",
    "iPhone 12 Pro Max", "iPhone 12 Pro", "iPhone 12", "iPhone 12 mini",
    "iPhone 11 Pro Max", "iPhone 11 Pro", "iPhone 11",
    "iPhone XS Max", "iPhone XS", "iPhone XR", "iPhone X",
    "iPhone 8 Plus", "iPhone 8", "iPhone 7 Plus", "iPhone 7",
    "iPhone SE (3-го поколения)", "iPhone SE (2-го поколения)",
    "Samsung Galaxy S25 Ultra", "Samsung Galaxy S25+", "Samsung Galaxy S25",
    "Samsung Galaxy S24 Ultra", "Samsung Galaxy S24+", "Samsung Galaxy S24",
    "Samsung Galaxy S23 Ultra", "Samsung Galaxy S23+", "Samsung Galaxy S23",
    "Samsung Galaxy A55", "Samsung Galaxy A54", "Samsung Galaxy A35", "Samsung Galaxy A34",
    "Samsung Galaxy A25", "Samsung Galaxy A15",
    "Xiaomi 14 Pro", "Xiaomi 14", "Xiaomi 13 Pro", "Xiaomi 13",
    "Redmi Note 13 Pro+", "Redmi Note 13 Pro", "Redmi Note 13",
    "Redmi Note 12 Pro+", "Redmi Note 12 Pro", "Redmi Note 12",
    "POCO X6 Pro", "POCO X6", "POCO X5 Pro", "POCO X5",
    "Другая модель",
  ],
  "Планшет": [
    "iPad Pro 12.9\" (M2)", "iPad Pro 12.9\" (M1)", "iPad Pro 11\" (M2)", "iPad Pro 11\" (M1)",
    "iPad Air 5", "iPad Air 4", "iPad Air 3",
    "iPad mini 6", "iPad mini 5",
    "iPad 10-го поколения", "iPad 9-го поколения", "iPad 8-го поколения",
    "Samsung Galaxy Tab S9 Ultra", "Samsung Galaxy Tab S9+", "Samsung Galaxy Tab S9",
    "Samsung Galaxy Tab S8 Ultra", "Samsung Galaxy Tab S8+", "Samsung Galaxy Tab S8",
    "Samsung Galaxy Tab A9+", "Samsung Galaxy Tab A9", "Samsung Galaxy Tab A8",
    "Другая модель",
  ],
  "Ноутбук": [
    "MacBook Air 15\" (M3)", "MacBook Air 13\" (M3)",
    "MacBook Air 15\" (M2)", "MacBook Air 13\" (M2)",
    "MacBook Air (M1)",
    "MacBook Pro 16\" (M3 Pro/Max)", "MacBook Pro 14\" (M3 Pro/Max)",
    "MacBook Pro 16\" (M2 Pro/Max)", "MacBook Pro 14\" (M2 Pro/Max)",
    "MacBook Pro 13\" (M2)", "MacBook Pro 13\" (M1)",
    "Asus VivoBook 15/16", "Asus ZenBook 14/15",
    "Lenovo IdeaPad 3/5", "Lenovo ThinkPad",
    "HP Laptop / Pavilion / Spectre",
    "Dell Inspiron / XPS",
    "Acer Aspire / Swift",
    "Другая модель",
  ],
  "ПК": [
    "Стационарный ПК (сборка)",
    "Моноблок",
    "Другая модель",
  ],
  "Другая техника": [
    "Apple Watch Ultra 2", "Apple Watch Series 9", "Apple Watch SE",
    "Samsung Galaxy Watch 6", "Samsung Galaxy Watch 5",
    "AirPods Pro 2", "AirPods 3", "AirPods 2",
    "Samsung Galaxy Buds",
    "PlayStation 5", "Xbox Series X/S", "Nintendo Switch",
    "Другое",
  ],
};

const deviceTypeSelect  = document.getElementById("deviceTypeSelect");
const deviceModelLabel  = document.getElementById("deviceModelLabel");
const deviceModelSelect = document.getElementById("deviceModelSelect");

if (deviceTypeSelect && deviceModelLabel && deviceModelSelect) {
  deviceTypeSelect.addEventListener("change", () => {
    const type   = deviceTypeSelect.value;
    const models = DEVICE_MODELS[type] || [];

    deviceModelSelect.innerHTML = '<option value="" disabled selected>Выберите модель</option>';
    models.forEach((m) => {
      const opt = document.createElement("option");
      opt.value    = m;
      opt.textContent = m;
      deviceModelSelect.appendChild(opt);
    });

    deviceModelLabel.style.display = models.length ? "" : "none";
    deviceModelSelect.required     = models.length > 0;
  });
}

/* ─────────────────────── Слоты времени ────────────────────────────────── */
const slotsContainer      = document.getElementById("slotsContainer");
const slotsToggleBtn      = document.getElementById("slotsToggleBtn");
const slotsSelectedLabel  = document.getElementById("slotsSelectedLabel");
const selectedSlotInput   = document.getElementById("selectedSlotInput");
const selectedSlotIdInput = document.getElementById("selectedSlotIdInput");
let slotsExpanded = false;

if (slotsToggleBtn) {
  slotsToggleBtn.addEventListener("click", () => {
    slotsExpanded = !slotsExpanded;
    slotsContainer.style.display = slotsExpanded ? "" : "none";
    slotsToggleBtn.textContent = slotsExpanded ? "▲ Скрыть слоты" : "▼ Выбрать время";
  });
}

const RU_DAYS   = ["вс","пн","вт","ср","чт","пт","сб"];
const RU_MONTHS = ["янв","фев","мар","апр","май","июн","июл","авг","сен","окт","ноя","дек"];

function fmtDate(iso) {
  const d = new Date(iso);
  return `${d.getDate()} ${RU_MONTHS[d.getMonth()]} (${RU_DAYS[d.getDay()]})`;
}
function fmtTime(iso) {
  const d = new Date(iso);
  return d.toLocaleTimeString("ru-RU", { hour: "2-digit", minute: "2-digit" });
}

function renderSlots(slots) {
  if (!slotsContainer) return;
  if (!slots || !slots.length) {
    slotsContainer.innerHTML = '<p class="slots-empty">Нет свободных слотов. Позвоните нам напрямую.</p>';
    return;
  }

  // Группируем по дате (YYYY-MM-DD)
  const byDay = {};
  slots.forEach((s) => {
    const key = new Date(s.slot_datetime).toISOString().slice(0, 10);
    (byDay[key] = byDay[key] || []).push(s);
  });

  const grid = document.createElement("div");
  grid.className = "slots-grid";

  for (const daySlots of Object.values(byDay)) {
    const wrap = document.createElement("div");
    wrap.className = "slot-day";

    const lbl = document.createElement("div");
    lbl.className = "slot-day-label";
    lbl.textContent = fmtDate(daySlots[0].slot_datetime);
    wrap.appendChild(lbl);

    const times = document.createElement("div");
    times.className = "slot-times";

    daySlots.forEach((s) => {
      const btn = document.createElement("button");
      btn.type          = "button";
      btn.className     = "slot-btn";
      btn.textContent   = fmtTime(s.slot_datetime);
      btn.dataset.slotId       = s.id;
      btn.dataset.slotDatetime = s.slot_datetime;

      btn.addEventListener("click", () => {
        slotsContainer.querySelectorAll(".slot-btn").forEach((b) => b.classList.remove("selected"));
        btn.classList.add("selected");
        if (selectedSlotInput)   selectedSlotInput.value   = s.slot_datetime;
        if (selectedSlotIdInput) selectedSlotIdInput.value = s.id;
        // Обновляем подпись кнопки и сворачиваем сетку
        const label = fmtDate(s.slot_datetime) + ", " + fmtTime(s.slot_datetime);
        if (slotsToggleBtn) {
          slotsToggleBtn.textContent = "✅ " + label + " (изменить)";
          slotsToggleBtn.classList.add("slot-chosen");
        }
        if (slotsSelectedLabel) slotsSelectedLabel.textContent = label;
        // Схлопываем после выбора
        slotsExpanded = false;
        slotsContainer.style.display = "none";
      });

      times.appendChild(btn);
    });

    wrap.appendChild(times);
    grid.appendChild(wrap);
  }

  slotsContainer.innerHTML = "";
  slotsContainer.appendChild(grid);
}

async function loadSlots() {
  if (!slotsContainer) return;
  slotsContainer.innerHTML = '<p class="slots-empty muted">Загрузка слотов…</p>';
  try {
    const res  = await fetch("/api/slots");
    const data = await res.json();
    if (data.ok) renderSlots(data.slots);
    else slotsContainer.innerHTML = '<p class="slots-empty">Ошибка загрузки слотов.</p>';
  } catch {
    slotsContainer.innerHTML = '<p class="slots-empty">Ошибка сети.</p>';
  }
}

loadSlots();

/* ─────────────────────── Прайс-лист ───────────────────────────────────── */
const priceTableBody = document.getElementById("priceTableBody");

async function loadPrices() {
  if (!priceTableBody) return;
  try {
    const res  = await fetch("/api/prices");
    const data = await res.json();
    if (!data.ok || !data.prices || !data.prices.length) {
      priceTableBody.innerHTML =
        '<tr><td colspan="2" style="text-align:center;padding:16px;" class="muted">Прайс временно недоступен</td></tr>';
      return;
    }

    const byCategory = {};
    data.prices.forEach((p) => {
      (byCategory[p.category] = byCategory[p.category] || []).push(p);
    });

    let html = "";
    for (const [cat, items] of Object.entries(byCategory)) {
      html += `<tr class="category"><td colspan="2">${esc(cat)}</td></tr>`;
      items.forEach((p) => {
        html += `<tr><td>${esc(p.service_name)}</td><td style="white-space:nowrap;">${esc(p.price_text)}</td></tr>`;
      });
    }
    priceTableBody.innerHTML = html;
  } catch {
    priceTableBody.innerHTML =
      '<tr><td colspan="2" style="text-align:center;padding:16px;" class="muted">Ошибка загрузки</td></tr>';
  }
}

loadPrices();

/* ─────────────────────── Форма записи на ремонт ───────────────────────── */
const repairForm      = document.getElementById("repairForm");
const repairStatusBox = document.getElementById("repairStatusBox");

if (repairForm) {
  repairForm.addEventListener("submit", async (e) => {
    e.preventDefault();

    const slotId       = selectedSlotIdInput ? selectedSlotIdInput.value : "";
    const slotDatetime = selectedSlotInput    ? selectedSlotInput.value   : "";

    if (!slotId) {
      showStatus(repairStatusBox, "err", "Пожалуйста, выберите удобное время из слотов выше.");
      return;
    }

    const fd  = new FormData(repairForm);
    const btn = repairForm.querySelector("button[type=submit]");
    if (btn) btn.disabled = true;

    try {
      const res = await fetch("/api/repair/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          initData:    tg ? tg.initData : "",
          name:        fd.get("name"),
          phone:       fd.get("phone"),
          deviceType:  fd.get("deviceType"),
          deviceModel: fd.get("deviceModel") || "",
          description: fd.get("description") || "",
          preferredTime: slotDatetime,
          slotId:      parseInt(slotId, 10),
        }),
      });
      const data = await res.json();
      if (data.ok) {
        showStatus(repairStatusBox, "ok", `✅ Заявка принята! Ваш номер: ${data.order_number}`);
        repairForm.reset();
        if (deviceModelLabel) deviceModelLabel.style.display = "none";
        if (selectedSlotInput)   selectedSlotInput.value   = "";
        if (selectedSlotIdInput) selectedSlotIdInput.value = "";
        if (slotsToggleBtn) {
          slotsToggleBtn.textContent = "▼ Выбрать время";
          slotsToggleBtn.classList.remove("slot-chosen");
        }
        if (slotsSelectedLabel) slotsSelectedLabel.textContent = "";
        slotsExpanded = false;
        if (slotsContainer) slotsContainer.style.display = "none";
        if (btn) btn.disabled = false;
        await loadSlots();
      } else {
        showStatus(repairStatusBox, "err", "Ошибка: " + (data.error || "Неизвестная ошибка"));
        if (btn) btn.disabled = false;
      }
    } catch {
      showStatus(repairStatusBox, "err", "Ошибка сети. Попробуйте ещё раз.");
      if (btn) btn.disabled = false;
    }
  });
}

/* ─────────────────────── Форма «Задать вопрос» ────────────────────────── */
const questionForm      = document.getElementById("questionForm");
const questionStatusBox = document.getElementById("questionStatusBox");

if (questionForm) {
  questionForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const fd  = new FormData(questionForm);
    const btn = questionForm.querySelector("button[type=submit]");
    if (btn) btn.disabled = true;

    try {
      const res = await fetch("/api/question/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          initData:     tg ? tg.initData : "",
          questionText: fd.get("questionText"),
        }),
      });
      const data = await res.json();
      if (data.ok) {
        showStatus(questionStatusBox, "ok", "✅ Вопрос отправлен! Ответим вам в Telegram.");
        questionForm.reset();
        if (btn) btn.disabled = false;
      } else {
        showStatus(questionStatusBox, "err", "Ошибка: " + (data.error || "Неизвестная ошибка"));
        if (btn) btn.disabled = false;
      }
    } catch {
      showStatus(questionStatusBox, "err", "Ошибка сети. Попробуйте ещё раз.");
      if (btn) btn.disabled = false;
    }
  });
}

/* ─────────────────────── Форма «Статус заявки» ────────────────────────── */
const statusForm = document.getElementById("statusForm");
const statusBox  = document.getElementById("statusBox");

const STATUS_LABELS = {
  new:         "🆕 Новая — ждёт приёма мастера",
  in_progress: "🔧 В работе — мастер занимается устройством",
  ready:       "✅ Готово — можно забирать!",
  done:        "🏁 Завершено — устройство выдано клиенту",
};

if (statusForm) {
  statusForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const fd          = new FormData(statusForm);
    const orderNumber = (fd.get("orderNumber") || "").trim();
    if (!orderNumber) return;

    const btn = statusForm.querySelector("button[type=submit]");
    if (btn) btn.disabled = true;

    try {
      const res  = await fetch("/api/repair/status?order=" + encodeURIComponent(orderNumber));
      const data = await res.json();
      if (data.ok && data.repair) {
        const r     = data.repair;
        const label = STATUS_LABELS[r.status] || r.status;
        let msg     = `${label}\n\n№ заявки: ${r.order_number}\nТип: ${r.device_type}`;
        if (r.device_model) msg += ` — ${r.device_model}`;
        showStatus(statusBox, "ok", msg);
      } else {
        showStatus(statusBox, "err", data.error || "Заявка не найдена. Проверьте номер.");
      }
    } catch {
      showStatus(statusBox, "err", "Ошибка сети. Попробуйте ещё раз.");
    }
    if (btn) btn.disabled = false;
  });
}

/* ─────────────────────── Helpers ──────────────────────────────────────── */
function showStatus(el, cls, text) {
  if (!el) return;
  el.className    = "status " + cls;
  el.style.display = "";
  el.textContent  = text;
}

function esc(str) {
  return String(str || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}
