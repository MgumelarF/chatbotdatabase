document.addEventListener("DOMContentLoaded", () => {

    /************** NAVIGASI **************/
    const sidebarToggle = document.querySelector(".sidebar-toggle");
    const sidebarMenuItems = document.querySelectorAll(".sidebar-menu li");
    const sections = document.querySelectorAll(".section");
    const logoutBtn = document.getElementById("logoutBtn");

    function showSection(id, el) {
        sections.forEach(sec => sec.classList.remove("active"));
        sidebarMenuItems.forEach(li => li.classList.remove("active"));

        const section = document.getElementById(id);
        if (section) section.classList.add("active");
        el.classList.add("active");
    }

    sidebarMenuItems.forEach(li => {
        li.addEventListener("click", () => {
            const sectionId = li.dataset.section;
            showSection(sectionId, li);
        });
    });

    sidebarToggle?.addEventListener("click", () => {
        document.getElementById("sidebar")?.classList.toggle("closed");
    });

    logoutBtn?.addEventListener("click", async () => {
        await fetch("/logout");
        window.location.href = "/admin/login";
    });

    /************** KATEGORI **************/
    let editCategoryId = null;
    let categoriesCache = [];

    async function loadCategoryOptions() {
        const res = await fetch("/categories");
        categoriesCache = await res.json();

        const select = document.getElementById("faqCategory");
        if (!select) return;

        select.innerHTML = "<option value=''>Pilih Kategori</option>";
        categoriesCache.forEach(cat => {
            const opt = document.createElement("option");
            opt.value = cat._id;
            opt.textContent = cat.name;
            select.appendChild(opt);
        });

        // isi filter kategori FAQ
        const filterSelect = document.getElementById("faqCategoryFilter");
        if (filterSelect) {
            filterSelect.innerHTML = `
                <option value="all">Semua Kategori</option>
                <option value="none">Tanpa Kategori</option>
            `;

            categoriesCache.forEach(cat => {
                const opt = document.createElement("option");
                opt.value = cat._id;
                opt.textContent = cat.name;
                filterSelect.appendChild(opt);
            });
        }
    }

    async function loadCategories() {
        const res = await fetch("/categories");
        const data = await res.json();

        const tbody = document.querySelector("#categoryTable tbody");
        if (!tbody) return;

        tbody.innerHTML = "";

        data.forEach(cat => {
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td>${cat._id}</td>
                <td>${cat.name}</td>
                <td>
                    <button class="editCatBtn">Edit</button>
                    <button class="delCatBtn">Hapus</button>
                </td>
            `;
            tbody.appendChild(tr);

            tr.querySelector(".editCatBtn").onclick = () => {
                editCategoryId = cat._id;
                document.getElementById("editCategoryName").value = cat.name;
                document.getElementById("editCategoryForm").style.display = "block";

                lockCategoryActions(tr);
            };

            tr.querySelector(".delCatBtn").onclick = async () => {
                if (!confirm("Hapus kategori ini?")) return;
                await fetch(`/categories/${cat._id}`, {
                    method: "DELETE",
                    credentials: "include"
                });
                loadCategories();
                loadFaq();
            };
        });

        loadCategoryOptions();
    }
    function lockCategoryActions(activeRow) {
        // lock tombol tambah kategori
        document.getElementById("addCategoryBtn").disabled = true;
        document.getElementById("newCategoryName").disabled = true;

        // lock semua tombol edit & hapus kategori
        document.querySelectorAll(".editCatBtn, .delCatBtn").forEach(btn => {
            btn.disabled = true;
        });

        // aktifkan kembali tombol edit di baris yang sedang diedit
        const editBtn = activeRow.querySelector(".editCatBtn");
        if (editBtn) editBtn.disabled = true; // tetap disable (sedang aktif)

        // highlight baris kategori
        activeRow.classList.add("editing");
    }


    function isValidCategoryName(name) {
        // minimal 3 karakter
        if (name.length < 3) return false;

        // hanya boleh huruf, angka, dan spasi
        // HARUS mengandung minimal 1 huruf
        const regex = /^(?=.*[a-zA-Z])[a-zA-Z0-9\s]+$/;
        return regex.test(name);
    }

    document.getElementById("addCategoryBtn")?.addEventListener("click", async () => {
        const input = document.getElementById("newCategoryName");
        const name = input.value.trim();

        if (!name) {
            alert("Nama kategori wajib diisi");
            return;
        }

        if (!isValidCategoryName(name)) {
            alert("Nama kategori tidak valid. Jangan asal mengetik.");
            return;
        }

        await fetch("/categories", {
            method: "POST",
            credentials: "include",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ name })
        });

        input.value = "";
        loadCategories();
        loadFaq();
    });

    document.getElementById("saveEditCategoryBtn")?.addEventListener("click", async () => {
        const name = document.getElementById("editCategoryName").value.trim();
        if (!name || !editCategoryId) return;

        await fetch(`/categories/${editCategoryId}`, {
            method: "PUT",
            credentials: "include",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ name })
        });

        editCategoryId = null;
        document.getElementById("editCategoryForm").style.display = "none";
        unlockCategoryActions();
        loadCategories();
        loadFaq();
    });

    document.getElementById("cancelEditCategoryBtn")?.addEventListener("click", () => {
        editCategoryId = null;
        document.getElementById("editCategoryForm").style.display = "none";
        unlockCategoryActions();
    });

    function unlockCategoryActions() {
        document.getElementById("addCategoryBtn").disabled = false;
        document.getElementById("newCategoryName").disabled = false;

        document.querySelectorAll(".editCatBtn, .delCatBtn").forEach(btn => {
            btn.disabled = false;
        });

        document.querySelectorAll("#categoryTable tr.editing").forEach(tr => {
            tr.classList.remove("editing");
        });
    }


    /************** FAQ **************/
    
    let faqs = [];
    let activeEditForm = null;
    let activeFaqDiv = null;
    let isDirtyEdit = false;
    let faqSearchKeyword = "";
    let faqCategoryFilter = "all";


    async function loadFaq() {
        const res = await fetch("/faq");
        faqs = await res.json();
        renderFaq();
    }

    async function saveFaq() {
        const q = document.getElementById("question").value.trim();
        const a = document.getElementById("answer").value.trim();
        const c = document.getElementById("faqCategory").value;

        if (!q) {
            return alert("Pertanyaan tidak boleh kosong");
        }
        if (!a) {
            return alert("Jawaban tidak boleh kosong");
        }
        if (!c) {
            return alert("Kategori harus dipilih");
        }

        await fetch("/faq", {
            method: "POST",
            credentials: "include",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ question: q, answer: a, category_id: c })
        });

        document.getElementById("question").value = "";
        document.getElementById("answer").value = "";
        document.getElementById("faqCategory").value = "";

        loadFaq();
    }

    function getCategoryName(id) {
        const cat = categoriesCache.find(c => c._id === id);
        return cat ? cat.name : "-";
    }

    function renderFaq() {
        const list = document.getElementById("faqList");
        if (!list) return;

        list.innerHTML = "";

        if (faqs.length === 0) {
            list.innerHTML = "<p>Belum ada FAQ.</p>";
            return;
        }

        faqs
        .filter(item => {
            // filter teks pertanyaan
            const matchText = item.question.toLowerCase().includes(faqSearchKeyword);

            // filter kategori
            let matchCategory = true;

            if (faqCategoryFilter === "none") {
                matchCategory = !item.category_id;
            } else if (faqCategoryFilter !== "all") {
                matchCategory = item.category_id === faqCategoryFilter;
            }

            return matchText && matchCategory;
        })
        .forEach((item, i) => {
            const div = document.createElement("div");
            div.innerHTML = `
                <b>${item.question}</b> <i>(${getCategoryName(item.category_id)})</i><br>
                ${item.answer}<br>
                <button class="editFaqBtn">Edit</button>
                <button class="delFaqBtn">Hapus</button>
                <hr>
            `;
            list.appendChild(div);

            div.querySelector(".editFaqBtn").onclick = () => editFaq(i, div);
            div.querySelector(".delFaqBtn").onclick = () => deleteFaq(i);
        });
    }

    function lockAddFaqForm() {
        document.getElementById("question").disabled = true;
        document.getElementById("answer").disabled = true;
        document.getElementById("faqCategory").disabled = true;
        document.getElementById("saveFaqBtn").disabled = true;

        document.getElementById("faqForm").style.opacity = "0.5";
    }

    function unlockAddFaqForm() {
        document.getElementById("question").disabled = false;
        document.getElementById("answer").disabled = false;
        document.getElementById("faqCategory").disabled = false;
        document.getElementById("saveFaqBtn").disabled = false;

        document.getElementById("faqForm").style.opacity = "1";
    }

    function lockFaqSearch() {
        document.getElementById("faqSearchInput").disabled = true;
        document.getElementById("faqCategoryFilter").disabled = true;
        document.getElementById("faqSearchBtn").disabled = true;
        document.getElementById("faqResetBtn").disabled = true;

        document.getElementById("faqFilter").style.opacity = "0.5";
    }

    function unlockFaqSearch() {
        document.getElementById("faqSearchInput").disabled = false;
        document.getElementById("faqCategoryFilter").disabled = false;
        document.getElementById("faqSearchBtn").disabled = false;
        document.getElementById("faqResetBtn").disabled = false;

        document.getElementById("faqFilter").style.opacity = "1";
    }

    function editFaq(i, faqDiv) {
        if (activeEditForm && isDirtyEdit) {
            const ok = confirm("Perubahan belum disimpan. Lanjutkan dan batalkan perubahan?");
            if (!ok) return;
        }

        if (activeEditForm) {
            activeEditForm.remove();
            activeEditForm = null;
        }

        if (activeFaqDiv) {
            activeFaqDiv.classList.remove("editing");
            const btn = activeFaqDiv.querySelector(".editFaqBtn");
            if (btn) btn.disabled = false;
        }

        isDirtyEdit = false;

        // Cari ID FAQ dari data yang ditampilkan
        // Kita perlu cara untuk menyimpan ID FAQ di elemen div
        // Tapi kode Anda belum menyimpannya
        
        // SOLUSI: Simpan FAQ ID sebagai data attribute di elemen FAQ
        // Pertama, ubah cara renderFaq untuk menyimpan ID:
    }

    // Ubah fungsi renderFaq bagian pembuatan elemen:
    function renderFaq() {
        const list = document.getElementById("faqList");
        if (!list) return;

        list.innerHTML = "";

        if (faqs.length === 0) {
            list.innerHTML = "<p>Belum ada FAQ.</p>";
            return;
        }

        const filteredFaqs = faqs.filter(item => {
            const matchText = item.question.toLowerCase().includes(faqSearchKeyword);
            let matchCategory = true;

            if (faqCategoryFilter === "none") {
                matchCategory = !item.category_id;
            } else if (faqCategoryFilter !== "all") {
                matchCategory = item.category_id === faqCategoryFilter;
            }

            return matchText && matchCategory;
        });

        filteredFaqs.forEach((item) => {
            const div = document.createElement("div");
            // Simpan ID FAQ sebagai data attribute
            div.setAttribute("data-faq-id", item._id);
            
            div.innerHTML = `
                <b>${item.question}</b> <i>(${getCategoryName(item.category_id)})</i><br>
                ${item.answer}<br>
                <button class="editFaqBtn">Edit</button>
                <button class="delFaqBtn">Hapus</button>
                <hr>
            `;
            list.appendChild(div);

            // Ubah fungsi editFaq untuk menggunakan ID
            div.querySelector(".editFaqBtn").onclick = () => {
                const faqId = div.getAttribute("data-faq-id");
                editFaqById(faqId, div);
            };
            
            div.querySelector(".delFaqBtn").onclick = () => {
                const faqId = div.getAttribute("data-faq-id");
                deleteFaqById(faqId);
            };
        });
    }


    async function deleteFaq(i) {
        if (!confirm("Hapus FAQ ini?")) return;
        await fetch(`/faq/${faqs[i]._id}`, {
            method: "DELETE",
            credentials: "include"
        });
        loadFaq();
    }

    document.getElementById("saveFaqBtn")?.addEventListener("click", saveFaq);
    document.getElementById("faqSearchBtn")?.addEventListener("click", () => {
        const keywordInput = document.getElementById("faqSearchInput");
        const categorySelect = document.getElementById("faqCategoryFilter");

        faqSearchKeyword = keywordInput.value.trim().toLowerCase();
        faqCategoryFilter = categorySelect.value;

        renderFaq();
    });
    document.getElementById("faqResetBtn")?.addEventListener("click", () => {
        document.getElementById("faqSearchInput").value = "";
        document.getElementById("faqCategoryFilter").value = "all";

        faqSearchKeyword = "";
        faqCategoryFilter = "all";

        renderFaq();
    });


    /************** INTENTS **************/
    async function loadIntents() {
        const res = await fetch("/intents");
        const data = await res.json();
        document.getElementById("intentsEditor").value = data.content || "";
    }

    document.getElementById("saveIntentsBtn")?.addEventListener("click", async () => {
        const content = document.getElementById("intentsEditor").value;
        try {
            JSON.parse(content);
        } catch {
            return alert("JSON tidak valid");
        }

        await fetch("/intents/update", {
            method: "POST",
            credentials: "include",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ content })
        });

        alert("Intents disimpan & chatbot direfresh");
    });

    /************** ADMIN USERS **************/
    async function loadUsers() {
        const res = await fetch("/admin/users");
        if (!res.ok) return;

        const users = await res.json();
        const list = document.getElementById("userList");
        if (!list) return;

        list.innerHTML = "";

        users.forEach(u => {
            const li = document.createElement("li");
            li.innerHTML = `${u.username} (${u.role}) <button>Hapus</button>`;
            li.querySelector("button").onclick = async () => {
                if (!confirm("Hapus user ini?")) return;
                await fetch(`/admin/users/${u._id}`, {
                    method: "DELETE",
                    credentials: "include"
                });
                loadUsers();
            };
            list.appendChild(li);
        });
    }

    document.getElementById("addUserBtn")?.addEventListener("click", async () => {
        const username = document.getElementById("newUsername").value.trim();
        const email = document.getElementById("newEmail").value.trim();
        const role = document.getElementById("newRole").value;

        if (!username || !email) return alert("Username dan email wajib");

        const res = await fetch("/admin/users/add", {
            method: "POST",
            credentials: "include",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username, email, role })
        });

        const data = await res.json();
        if (data.success) {
            alert("Admin ditambahkan & email terkirim");
            loadUsers();
        } else {
            alert(data.error);
        }
    });

    /************** LOAD AWAL **************/
    loadCategories().then(loadFaq);
    loadIntents();
    loadUsers();

});