document.getElementById("loginBtn").addEventListener("click", function () {
    const username = document.getElementById("username").value.trim();
    const password = document.getElementById("password").value.trim();
    const errorMsg = document.getElementById("errorMsg");

    // Sembunyikan error setiap klik
    errorMsg.style.display = "none";

    // Validasi sederhana
    if (!username || !password) {
        errorMsg.innerText = "Username dan password wajib diisi";
        errorMsg.style.display = "block";
        return;
    }

    fetch("/login", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            username: username,
            password: password
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // INI KUNCI UTAMANYA
            window.location.href = "/dashboard";
        } else {
            errorMsg.innerText = "Username atau password salah";
            errorMsg.style.display = "block";
        }
    })
    .catch(err => {
        errorMsg.innerText = "Server error";
        errorMsg.style.display = "block";
        console.error(err);
    });
});
