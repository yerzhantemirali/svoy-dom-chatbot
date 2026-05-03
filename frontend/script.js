const API_BASE_URL = "http://localhost:8000";

const phoneInput = document.getElementById("phoneInput");
const createChatBtn = document.getElementById("createChatBtn");
const chatListEl = document.getElementById("chatList");
const chatHeader = document.getElementById("chatHeader");
const messagesEl = document.getElementById("messages");
const messageForm = document.getElementById("messageForm");
const messageInput = document.getElementById("messageInput");

let activePhone = "";
let chats = [];
let currentMessages = [];
let isLoading = false;

function renderChats() {
  chatListEl.innerHTML = "";
  if (!chats.length) {
    const empty = document.createElement("div");
    empty.className = "empty";
    empty.textContent = "Пока нет чатов";
    chatListEl.appendChild(empty);
    return;
  }

  chats.forEach((phone) => {
    const btn = document.createElement("button");
    btn.className = `chat-list-item ${phone === activePhone ? "active" : ""}`;
    btn.textContent = phone;
    btn.addEventListener("click", () => selectChat(phone));
    chatListEl.appendChild(btn);
  });
}

function renderMessages(messages) {
  messagesEl.innerHTML = "";
  if (!messages.length) {
    const empty = document.createElement("div");
    empty.className = "empty";
    empty.textContent = "Начните диалог";
    messagesEl.appendChild(empty);
  } else {
    messages.forEach((msg) => {
      const row = document.createElement("div");
      const isUser = msg.role === "user";
      row.className = `message-row ${isUser ? "user" : "assistant"}`;

      const bubble = document.createElement("div");
      bubble.className = `bubble ${isUser ? "bubble-user" : "bubble-assistant"}`;
      bubble.textContent = msg.content;
      row.appendChild(bubble);
      messagesEl.appendChild(row);
    });
  }

  if (isLoading) {
    const row = document.createElement("div");
    row.className = "message-row assistant";

    const bubble = document.createElement("div");
    bubble.className = "bubble bubble-assistant typing-bubble";
    bubble.innerHTML = `
      <span class="typing-dot"></span>
      <span class="typing-dot"></span>
      <span class="typing-dot"></span>
    `;
    row.appendChild(bubble);
    messagesEl.appendChild(row);
  }

  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function appendSystem(text) {
  const item = document.createElement("div");
  item.className = "system";
  item.textContent = text;
  messagesEl.appendChild(item);
}

async function fetchChats() {
  const res = await fetch(`${API_BASE_URL}/chats`);
  if (!res.ok) return;
  const data = await res.json();
  chats = data.phones || [];
  renderChats();
  if (!activePhone && chats.length) {
    await selectChat(chats[0]);
  }
}

async function selectChat(phone) {
  const res = await fetch(`${API_BASE_URL}/chats/${encodeURIComponent(phone)}`);
  if (!res.ok) return;
  const data = await res.json();

  activePhone = data.phone;
  currentMessages = data.messages || [];
  chatHeader.textContent = activePhone;
  messageForm.classList.remove("hidden");
  renderMessages(currentMessages);
  renderChats();

  if (data.paused) appendSystem("Бот на паузе. Менеджер скоро свяжется с вами.");
}

async function createChat() {
  const phone = phoneInput.value.trim();
  if (!phone) return;

  const res = await fetch(`${API_BASE_URL}/chats`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ phone }),
  });

  if (!res.ok) {
    appendSystem("Не удалось создать чат");
    return;
  }

  const data = await res.json();
  if (!chats.includes(data.phone)) chats.unshift(data.phone);
  phoneInput.value = "";
  await selectChat(data.phone);
}

async function sendMessage(event) {
  event.preventDefault();
  if (!activePhone) return;

  const text = messageInput.value.trim();
  if (!text) return;

  currentMessages = [...currentMessages, { role: "user", content: text }];
  renderMessages(currentMessages);
  messageInput.value = "";
  isLoading = true;
  renderMessages(currentMessages);

  try {
    const res = await fetch(`${API_BASE_URL}/chats/${encodeURIComponent(activePhone)}/messages`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    });

    if (!res.ok) {
      appendSystem("Ошибка запроса");
      return;
    }

    const data = await res.json();
    if (data.response) {
      currentMessages = [...currentMessages, { role: "assistant", content: data.response }];
      renderMessages(currentMessages);
    } else {
      appendSystem("Бот на паузе. Менеджер скоро свяжется с вами.");
    }
  } finally {
    isLoading = false;
    renderMessages(currentMessages);
  }
}

createChatBtn.addEventListener("click", createChat);
messageForm.addEventListener("submit", sendMessage);

fetchChats();
