// Telegram Mini App SDK
const tg = window.Telegram ? window.Telegram.WebApp : null;

if (tg) {
  tg.ready();
  tg.expand();
}

function showStatus(el, kind, text) {
  el.style.display = "block";
  el.classList.remove("ok", "err");
  if (kind === "ok") el.classList.add("ok");
  if (kind === "err") el.classList.add("err");
  el.textContent = text;
}

const initData = tg && tg.initData ? tg.initData : "";

// Подключаем тему Telegram (если доступно)
try {
  if (tg && tg.themeParams) {
    const theme = tg.themeParams;
    const root = document.documentElement;
    if (theme.bg_color) root.style.setProperty("--tg-theme-bg-color", theme.bg_color);
    if (theme.text_color) root.style.setProperty("--tg-theme-text-color", theme.text_color);
    if (theme.hint_color) root.style.setProperty("--tg-theme-hint-color", theme.hint_color);
  }
} catch (_) {}

// Навигация по вкладкам
const tabs = document.querySelectorAll(".nav button");
const tabSections = document.querySelectorAll(".tab");

function setTab(tabName) {
  tabs.forEach(b => b.classList.toggle("active", b.dataset.tab === tabName));
  tabSections.forEach(s => {
    const id = s.id.replace("tab-", "");
    s.style.display = id === tabName ? "" : "none";
  });
}

tabs.forEach(btn => {
  btn.addEventListener("click", () => setTab(btn.dataset.tab));
});

// Инфо о пользователе
try {
  if (tg && tg.initDataUnsafe && tg.initDataUnsafe.user) {
    const u = tg.initDataUnsafe.user;
    const line = u.username ? "@" + u.username : "Пользователь";
    document.getElementById("tgUserLine").textContent = line;
  }
} catch (_) {}

// Общая функция для POST-запросов к API
async function apiPost(url, body) {
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok || data.ok === false) {
    const err = data.error || "Ошибка запроса";
    throw new Error(err);
  }
  return data;
}

// Запись на ремонт
const repairForm = document.getElementById("repairForm");
const repairStatusBox = document.getElementById("repairStatusBox");
repairForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  try {
    repairStatusBox.textContent = "";
    const fd = new FormData(repairForm);
    const payload = {
      initData,
      name: fd.get("name"),
      phone: fd.get("phone"),
      deviceType: fd.get("deviceType"),
      description: fd.get("description"),
      preferredTime: fd.get("preferredTime"),
    };
    const data = await apiPost("/api/repair/register", payload);
    showStatus(repairStatusBox, "ok", `Заявка отправлена! Номер: ${data.order_number}`);
  } catch (err) {
    showStatus(repairStatusBox, "err", err.message || "Ошибка");
  }
});

// Вопрос администратору
const questionForm = document.getElementById("questionForm");
const questionStatusBox = document.getElementById("questionStatusBox");
questionForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  try {
    questionStatusBox.textContent = "";
    const fd = new FormData(questionForm);
    const payload = {
      initData,
      questionText: fd.get("questionText"),
    };
    const data = await apiPost("/api/question/ask", payload);
    showStatus(questionStatusBox, "ok", `Вопрос отправлен! №: ${data.question_id}. Администратор ответит вам в Telegram.`);
  } catch (err) {
    showStatus(questionStatusBox, "err", err.message || "Ошибка");
  }
});

// Проверка статуса ремонта
const statusForm = document.getElementById("statusForm");
const statusBox = document.getElementById("statusBox");
statusForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  try {
    statusBox.textContent = "";
    const fd = new FormData(statusForm);
    const payload = { orderNumber: fd.get("orderNumber") };
    const data = await apiPost("/api/repair/status", payload);
    showStatus(statusBox, "ok", `Заявка ${data.order_number}: ${data.status}`);
  } catch (err) {
    showStatus(statusBox, "err", err.message || "Ошибка");
  }
});
