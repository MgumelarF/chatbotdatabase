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
                if (!confirm("menghapus kategori menyebabkan hilangnya kategori pada faq, apakah anda yakin menghapus kategori ini?")) return;
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
        document.getElementById("addCategoryBtn").disabled = true;
        document.getElementById("newCategoryName").disabled = true;

        document.querySelectorAll(".editCatBtn, .delCatBtn").forEach(btn => {
            btn.disabled = true;
        });

        const editBtn = activeRow.querySelector(".editCatBtn");
        if (editBtn) editBtn.disabled = true;

        activeRow.classList.add("editing");
    }

    function isValidCategoryName(name) {
        if (name.length < 3) return false;
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
        if (!id) return "-";  //
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
            div.setAttribute("data-faq-id", item._id);
            
            div.innerHTML = `
                <b>${item.question}</b> <i>(${getCategoryName(item.category_id)})</i><br>
                ${item.answer}<br>
                <button class="editFaqBtn">Edit</button>
                <button class="delFaqBtn">Hapus</button>
                <hr>
            `;
            list.appendChild(div);

            div.querySelector(".editFaqBtn").onclick = () => editFaqById(item._id, div);
            div.querySelector(".delFaqBtn").onclick = () => deleteFaqById(item._id);
        });
    }

    function editFaqById(faqId, faqDiv) {
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

        // Dapatkan data FAQ yang akan diedit
        const faqToEdit = faqs.find(f => f._id === faqId);
        if (!faqToEdit) {
             alert("FAQ tidak ditemukan. Mungkin sudah dihapus.");
             return;
        }

        // Lock form tambah FAQ dan search
        lockAddFaqForm();
        lockFaqSearch();

        // Highlight FAQ yang sedang diedit
        faqDiv.classList.add("editing");
        activeFaqDiv = faqDiv;
        const editBtn = faqDiv.querySelector(".editFaqBtn");
        if (editBtn) editBtn.disabled = true;

        // Buat form edit
        const editForm = document.createElement("div");
        editForm.className = "faq-edit-form";
        editForm.innerHTML = `
            <h4>Edit FAQ</h4>
            <input type="text" class="edit-question" value="${faqToEdit.question}" placeholder="Pertanyaan">
            <textarea class="edit-answer" placeholder="Jawaban">${faqToEdit.answer}</textarea>
            <select class="edit-category">
                <option value="">Pilih Kategori</option>
                ${categoriesCache.map(cat => 
                    `<option value="${cat._id}" ${cat._id === faqToEdit.category_id ? 'selected' : ''}>${cat.name}</option>`
                ).join('')}
            </select>
            <div style="margin-top:10px;">
                <button class="save-edit-btn">Simpan</button>
                <button class="cancel-edit-btn">Batal</button>
            </div>
            <hr>
        `;

        faqDiv.parentNode.insertBefore(editForm, faqDiv.nextSibling);
        activeEditForm = editForm;

        // Tambah event listeners untuk form edit
        editForm.querySelector(".save-edit-btn").onclick = async () => {
            const newQuestion = editForm.querySelector(".edit-question").value.trim();
            const newAnswer = editForm.querySelector(".edit-answer").value.trim();
            const newCategory = editForm.querySelector(".edit-category").value;

            if (!newQuestion || !newAnswer || !newCategory) {
                alert("Semua field harus diisi");
                return;
            }

            try {
                await fetch(`/faq/${faqId}`, {
                    method: "PUT",
                    credentials: "include",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        question: newQuestion,
                        answer: newAnswer,
                        category_id: newCategory
                    })
                });

                activeEditForm.remove();
                activeEditForm = null;
                unlockAddFaqForm();
                unlockFaqSearch();
                faqDiv.classList.remove("editing");
                if (editBtn) editBtn.disabled = false;
                activeFaqDiv = null;

                loadFaq();
            } catch (error) {
                alert("Gagal menyimpan perubahan: " + error.message);
            }
        };

        editForm.querySelector(".cancel-edit-btn").onclick = () => {
            activeEditForm.remove();
            activeEditForm = null;
            unlockAddFaqForm();
            unlockFaqSearch();
            faqDiv.classList.remove("editing");
            if (editBtn) editBtn.disabled = false;
            activeFaqDiv = null;
        };

        // Deteksi perubahan untuk konfirmasi
        editForm.querySelectorAll(".edit-question, .edit-answer, .edit-category").forEach(input => {
            input.addEventListener("input", () => {
                isDirtyEdit = true;
            });
        });
    }

    async function deleteFaqById(faqId) {
        if (!confirm("Hapus FAQ ini?")) return;
        
        try {
            // 🔥 CEK APAKAH FAQ YANG AKAN DIHAPUS SEDANG DALAM MODE EDIT
            const isDeletingEditedFaq = activeFaqDiv && 
                activeFaqDiv.getAttribute("data-faq-id") === faqId;
            
            // 🔥 HAPUS FORM EDIT JIKA FAQ YANG DIHAPUS SAMA DENGAN YANG SEDANG DEDIT
            if (isDeletingEditedFaq && activeEditForm) {
                activeEditForm.remove();
                activeEditForm = null;
                
                // 🔥 UNLOCK FORM TAMBAH & SEARCH
                unlockAddFaqForm();
                unlockFaqSearch();
                
                // 🔥 RESET STATE EDIT
                if (activeFaqDiv) {
                    activeFaqDiv.classList.remove("editing");
                    const editBtn = activeFaqDiv.querySelector(".editFaqBtn");
                    if (editBtn) editBtn.disabled = false;
                    activeFaqDiv = null;
                }
                
                isDirtyEdit = false;
            }
            
            // 🔥 HAPUS FAQ DARI SERVER
            await fetch(`/faq/${faqId}`, {
                method: "DELETE",
                credentials: "include"
            });
            
            // 🔥 LOAD ULANG FAQ
            await loadFaq();
            
        } catch (error) {
            alert("Gagal menghapus FAQ: " + error.message);
        }
    }

    function lockAddFaqForm() {
        const questionInput = document.getElementById("question");
        const answerInput = document.getElementById("answer");
        const categorySelect = document.getElementById("faqCategory");
        const saveBtn = document.getElementById("saveFaqBtn");
        const faqForm = document.getElementById("faqForm");

        if (questionInput) questionInput.disabled = true;
        if (answerInput) answerInput.disabled = true;
        if (categorySelect) categorySelect.disabled = true;
        if (saveBtn) saveBtn.disabled = true;
        if (faqForm) faqForm.style.opacity = "0.5";
    }

    function resetEditForm() {
        if (activeEditForm) {
            activeEditForm.remove();
            activeEditForm = null;
        }
        
        if (activeFaqDiv) {
            activeFaqDiv.classList.remove("editing");
            const editBtn = activeFaqDiv.querySelector(".editFaqBtn");
            if (editBtn) editBtn.disabled = false;
            activeFaqDiv = null;
        }
        
        isDirtyEdit = false;
        unlockAddFaqForm();
        unlockFaqSearch();
    }

    function unlockAddFaqForm() {
        const questionInput = document.getElementById("question");
        const answerInput = document.getElementById("answer");
        const categorySelect = document.getElementById("faqCategory");
        const saveBtn = document.getElementById("saveFaqBtn");
        const faqForm = document.getElementById("faqForm");

        if (questionInput) questionInput.disabled = false;
        if (answerInput) answerInput.disabled = false;
        if (categorySelect) categorySelect.disabled = false;
        if (saveBtn) saveBtn.disabled = false;
        if (faqForm) faqForm.style.opacity = "1";
    }

    function lockFaqSearch() {
        const searchInput = document.getElementById("faqSearchInput");
        const categoryFilter = document.getElementById("faqCategoryFilter");
        const searchBtn = document.getElementById("faqSearchBtn");
        const resetBtn = document.getElementById("faqResetBtn");
        const filterDiv = document.getElementById("faqFilter");

        if (searchInput) searchInput.disabled = true;
        if (categoryFilter) categoryFilter.disabled = true;
        if (searchBtn) searchBtn.disabled = true;
        if (resetBtn) resetBtn.disabled = true;
        if (filterDiv) filterDiv.style.opacity = "0.5";
    }

    function unlockFaqSearch() {
        const searchInput = document.getElementById("faqSearchInput");
        const categoryFilter = document.getElementById("faqCategoryFilter");
        const searchBtn = document.getElementById("faqSearchBtn");
        const resetBtn = document.getElementById("faqResetBtn");
        const filterDiv = document.getElementById("faqFilter");

        if (searchInput) searchInput.disabled = false;
        if (categoryFilter) categoryFilter.disabled = false;
        if (searchBtn) searchBtn.disabled = false;
        if (resetBtn) resetBtn.disabled = false;
        if (filterDiv) filterDiv.style.opacity = "1";
    }

    document.getElementById("saveFaqBtn")?.addEventListener("click", saveFaq);
    
    document.getElementById("faqSearchBtn")?.addEventListener("click", () => {
        const keywordInput = document.getElementById("faqSearchInput");
        const categorySelect = document.getElementById("faqCategoryFilter");

        if (keywordInput) faqSearchKeyword = keywordInput.value.trim().toLowerCase();
        if (categorySelect) faqCategoryFilter = categorySelect.value;

        renderFaq();
    });
    
    document.getElementById("faqResetBtn")?.addEventListener("click", () => {
        const keywordInput = document.getElementById("faqSearchInput");
        const categorySelect = document.getElementById("faqCategoryFilter");

        if (keywordInput) keywordInput.value = "";
        if (categorySelect) categorySelect.value = "all";

        faqSearchKeyword = "";
        faqCategoryFilter = "all";

        renderFaq();
    });

    /************** INTENTS **************/
    async function loadIntents() {
        const res = await fetch("/intents");
        const data = await res.json();
        const editor = document.getElementById("intentsEditor");
        if (editor) editor.value = data.content || "";
    }

    document.getElementById("saveIntentsBtn")?.addEventListener("click", async () => {
        const editor = document.getElementById("intentsEditor");
        if (!editor) return;
        
        const content = editor.value;
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
            li.innerHTML = `${u.username} (${u.role}) <button class="delete-user-btn">Hapus</button>`;
            list.appendChild(li);

            li.querySelector(".delete-user-btn").onclick = async () => {
                if (!confirm("Hapus user ini?")) return;
                await fetch(`/admin/users/${u._id}`, {
                    method: "DELETE",
                    credentials: "include"
                });
                loadUsers();
            };
        });
    }

    document.getElementById("addUserBtn")?.addEventListener("click", async () => {
        const usernameInput = document.getElementById("newUsername");
        const emailInput = document.getElementById("newEmail");
        const roleSelect = document.getElementById("newRole");

        if (!usernameInput || !emailInput || !roleSelect) return;

        const username = usernameInput.value.trim();
        const email = emailInput.value.trim();
        const role = roleSelect.value;

        if (!username || !email) {
            return alert("Username dan email wajib");
        }

        const res = await fetch("/admin/users/add", {
            method: "POST",
            credentials: "include",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username, email, role })
        });

        const data = await res.json();
        if (data.success) {
            alert("Admin ditambahkan & email terkirim");
            usernameInput.value = "";
            emailInput.value = "";
            roleSelect.value = "admin";
            loadUsers();
        } else {
            alert(data.error || "Terjadi kesalahan");
        }
    });


    /************** BACKUP FUNCTIONS **************/
    async function downloadBackup(url, defaultFilename) {
        try {
            // 🔥 TAMBAHKAN: Loading sederhana tanpa disable button
            const originalTitle = document.title;
            document.title = "⏳ Membuat backup...";
            
            // Fetch backup data
            const response = await fetch(url, {
                credentials: "include"
            });
            
            if (!response.ok) {
                // Coba baca error message dari response
                let errorMessage = `HTTP error! status: ${response.status}`;
                try {
                    const errorData = await response.json();
                    if (errorData.error) {
                        errorMessage = errorData.error;
                    }
                } catch {
                    // Jika response bukan JSON, gunakan status text
                    errorMessage = `${response.status}: ${response.statusText}`;
                }
                throw new Error(errorMessage);
            }
            
            // Get filename from header or use default
            let filename = defaultFilename;
            const contentDisposition = response.headers.get('Content-Disposition');
            
            if (contentDisposition) {
                const match = contentDisposition.match(/filename="(.+)"/);
                if (match && match[1]) {
                    filename = match[1];
                }
            }
            
            // Create download
            const blob = await response.blob();
            const blobUrl = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = blobUrl;
            link.download = filename;
            
            // Trigger download
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            
            // Cleanup
            window.URL.revokeObjectURL(blobUrl);
            
            // 🔥 TAMBAHKAN: Notifikasi sukses yang lebih informatif
            setTimeout(() => {
                alert(`✅ Backup berhasil didownload!\n\nFile: ${filename}\nSize: ${(blob.size / 1024).toFixed(2)} KB`);
            }, 300);
            
        } catch (error) {
            console.error('Download error:', error);
            alert(`❌ Gagal membuat backup\n\nError: ${error.message}\n\nPastikan Anda masih login dan coba lagi.`);
        } finally {
            // 🔥 RESET: Kembalikan title
            document.title = originalTitle;
        }
    }

    // Event listeners yang sederhana
    document.getElementById("backupCategoriesBtn")?.addEventListener("click", () => {
        downloadBackup("/backup/categories", "categories_backup.json");
    });

    document.getElementById("backupFaqBtn")?.addEventListener("click", () => {
        downloadBackup("/backup/faq", "faq_backup.json");
    });

    document.getElementById("backupAllBtn")?.addEventListener("click", () => {
        downloadBackup("/backup/all", "full_backup.json");
    });

    /************** LOAD AWAL **************/
    loadCategories().then(loadFaq);
    loadIntents();
    loadUsers();

});