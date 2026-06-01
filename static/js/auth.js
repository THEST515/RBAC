document.addEventListener("DOMContentLoaded", () => {
    const loginForm = document.getElementById("loginForm");
    const registerForm = document.getElementById("registerForm");

    if (loginForm) {
        loginForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const username = document.getElementById("username").value.trim();
            const password = document.getElementById("password").value;
            const errorEl = document.getElementById("loginError");

            try {
                const resp = await apiPost("/api/auth/login", { username, password });
                if (!resp) return;
                const data = await resp.json();
                if (!resp.ok) {
                    errorEl.textContent = data.error || "登录失败";
                    errorEl.classList.remove("d-none");
                    return;
                }
                errorEl.classList.add("d-none");
                RBAC.setAuth(data.token, data.user);
                window.location.href = "/";
            } catch (err) {
                errorEl.textContent = "网络错误，请重试";
                errorEl.classList.remove("d-none");
            }
        });
    }

    if (registerForm) {
        registerForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const username = document.getElementById("username").value.trim();
            const email = document.getElementById("email").value.trim();
            const password = document.getElementById("password").value;
            const confirmPassword = document.getElementById("confirmPassword").value;
            const errorEl = document.getElementById("registerError");

            errorEl.classList.add("d-none");

            if (password !== confirmPassword) {
                errorEl.textContent = "两次密码不一致";
                errorEl.classList.remove("d-none");
                return;
            }

            try {
                const resp = await apiPost("/api/auth/register", {
                    username,
                    password,
                    email: email || null,
                });
                if (!resp) return;
                const data = await resp.json();
                if (!resp.ok) {
                    errorEl.textContent = data.error || "注册失败";
                    errorEl.classList.remove("d-none");
                    return;
                }
                RBAC.setAuth(data.token, data.user);
                window.location.href = "/";
            } catch (err) {
                errorEl.textContent = "网络错误，请重试";
                errorEl.classList.remove("d-none");
            }
        });
    }
});
