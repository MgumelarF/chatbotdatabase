/************** NAVIGASI **************/
function showSection(id, el) {
    document.querySelectorAll(".section").forEach(sec => {
        sec.classList.remove("active");
    });

    document.querySelectorAll(".sidebar-menu li").forEach(li => {
        li.classList.remove("active");
    });

    document.getElementById(id).classList.add("active");
    el.classList.add("active");
}

function toggleSidebar() {
    document.getElementById("sidebar").classList.toggle("closed");
}

function logout() {
    window.location.href = "/logout";
}

/************** FAQ **************/
let faqs = [];
let editIndex = null;

function loadFaq() {
    fetch("/faq")
        .then(res => res.json())
        .then(data => {
            faqs = data;
            renderFaq();
        });
}

function renderFaq() {
    const list = document.getElementById("faqList");
    list.innerHTML = "";

    if (faqs.length === 0) {
        list.innerHTML = "<p>Belum ada FAQ.</p>";
        return;
    }

    faqs.forEach((item, i) => {
        list.innerHTML += `
            <div>
                <b>${item.question}</b><br>
                ${item.answer}<br>
                <button onclick="editFaq(${i})">Edit</button>
                <button onclick="deleteFaq(${i})">Hapus</button>
            </div>
            <hr>
        `;
    });
}

function saveFaq() {
    const q = document.getElementById("question").value.trim();
    const a = document.getElementById("answer").value.trim();

    if (!q || !a) {
        alert("Tidak boleh kosong");
        return;
    }

    if (editIndex === null) {
        faqs.push({ question: q, answer: a });
    } else {
        faqs[editIndex] = { question: q, answer: a };
        editIndex = null;
    }

    updateServer();
    document.getElementById("question").value = "";
    document.getElementById("answer").value = "";
}

function editFaq(i) {
    document.getElementById("question").value = faqs[i].question;
    document.getElementById("answer").value = faqs[i].answer;
    editIndex = i;
}

function deleteFaq(i) {
    if (confirm("Hapus FAQ ini?")) {
        faqs.splice(i, 1);
        updateServer();
    }
}

function updateServer() {
    fetch("/faq/update", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(faqs)
    }).then(loadFaq);
}

/************** INTENTS **************/
function loadIntents() {
    fetch("/intents")
        .then(res => res.json())
        .then(data => {
            document.getElementById("intentsEditor").value = data.content;
        });
}

function saveIntents() {
    const content = document.getElementById("intentsEditor").value;

    try {
        JSON.parse(content);
    } catch {
        alert("JSON tidak valid");
        return;
    }

    fetch("/intents/update", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ content })
    })
    .then(res => res.json())
    .then(() => alert("Intents disimpan & AI dilatih ulang"));
}

/************** LOAD **************/
loadFaq();
loadIntents();
