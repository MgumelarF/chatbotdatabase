const sidebar = document.getElementById("categoryList");
const faqContent = document.getElementById("faqContent");

let categories = [];
let faqs = [];

// ==============================
// LOAD DATA DARI SERVER
// ==============================

async function loadFaq() {
    const res = await fetch("/faq");
    faqs = await res.json();
    console.log("FAQ:", faqs);
}

async function loadCategories() {
    const res = await fetch("/categories");
    categories = await res.json();
    console.log("CATEGORIES:", categories);
    renderSidebar();
}

// ==============================
// RENDER SIDEBAR
// ==============================

function renderSidebar() {
    sidebar.innerHTML = "";

    if (categories.length === 0) {
        sidebar.innerHTML = "<li>Tidak ada kategori</li>";
        return;
    }

    categories.forEach(cat => {
        const li = document.createElement("li");
        li.textContent = cat.name;
        li.dataset.catId = cat._id;

        const ul = document.createElement("ul");
        ul.style.display = "none";

        faqs
            .filter(f => f.category_id === cat._id)
            .forEach(f => {
                const liFaq = document.createElement("li");
                liFaq.textContent = f.question;
                liFaq.addEventListener("click", e => {
                    e.stopPropagation();
                    showFaqDetail(f);
                });
                ul.appendChild(liFaq);
            });

        li.appendChild(ul);

        li.addEventListener("click", () => {
            ul.style.display = ul.style.display === "block" ? "none" : "block";
        });

        sidebar.appendChild(li);
    });
}

// ==============================
// TAMPILKAN FAQ
// ==============================

function showFaqDetail(faq) {
    faqContent.innerHTML = `
        <div class="faq-card">
            <h3>${faq.question}</h3>
            <p>${faq.answer}</p>
        </div>
    `;
}

// ==============================
// HELPER (OPSIONAL)
// ==============================

function getCategoryName(category_id) {
    const cat = categories.find(c => c._id === category_id);
    return cat ? cat.name : "Umum";
}

// ==============================
// INIT
// ==============================

async function initFAQ() {
    await loadFaq();        // WAJIB dulu
    await loadCategories(); // baru render
}

initFAQ();