const chatBtn = document.getElementById("chatButton");
const chatBox = document.getElementById("chatBox");
const chatContent = document.getElementById("chatContent");
const input = document.getElementById("userMessage");
const sendBtn = document.getElementById("sendBtn");
const closeChat = document.getElementById("closeChat");
const hamburgerBtn = document.getElementById("hamburgerBtn");
const menu = document.getElementById("menu");

// WAJIB ADA — supaya greeting muncul HANYA setelah klik tombol
let firstOpen = true;

function addMessage(sender, text) {
    const row = document.createElement("div");
    row.className = sender === "user" ? "user-row" : "bot-row";

    const bubble = document.createElement("div");
    bubble.className = sender === "user" ? "bubble-user" : "bubble-bot";
    bubble.textContent = text;

    row.appendChild(bubble);
    chatContent.appendChild(row);
    chatContent.scrollTop = chatContent.scrollHeight;
}

async function sendMessage() {
    const message = input.value.trim();
    if (!message) return;

    addMessage("user", message);
    input.value = "";

    const loading = document.createElement("div");
    loading.className = "bot-row";
    loading.innerHTML = `<div class="bubble-bot">Bot sedang mengetik...</div>`;
    chatContent.appendChild(loading);

    try {
        const res = await fetch("/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message })
        });

        const data = await res.json();
        chatContent.removeChild(loading);
        addMessage("bot", data.response);

    } catch (err) {
        chatContent.removeChild(loading);
        addMessage("bot", "⚠️ Tidak dapat terhubung ke server Python.");
    }
}

sendBtn.addEventListener("click", sendMessage);

input.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
        e.preventDefault();
        sendMessage();
    }
});

// ===== NOTIFIKASI CHATBOT =====
const chatNotif = document.getElementById("chatNotif");

// Langsung tampil saat halaman dibuka
chatNotif.style.display = "block";

// Toggle chat + hilangkan notif saat dibuka
chatBtn.addEventListener("click", () => {
    if (chatBox.style.display !== "flex") {
        chatBox.style.display = "flex";
        chatNotif.style.display = "none"; // notif hilang setelah dibuka

        if (firstOpen) {
            setTimeout(() => {
                addMessage("bot", "👋 Halo! Ada yang bisa saya bantu hari ini?");
            }, 150);
            firstOpen = false;
        }
    } else {
        chatBox.style.display = "none";
    }
});

// Tombol X untuk menutup chat
closeChat.addEventListener("click", () => {
    chatBox.style.display = "none";

    setTimeout(() => {
        chatNotif.style.display = "block";
    }, 2000);
});