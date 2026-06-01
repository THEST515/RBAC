const RBAC = {
    token: localStorage.getItem("rbac_token"),
    user: JSON.parse(localStorage.getItem("rbac_user") || "null"),

    setAuth(token, user) {
        this.token = token;
        this.user = user;
        localStorage.setItem("rbac_token", token);
        localStorage.setItem("rbac_user", JSON.stringify(user));
        this.updateUI();
    },

    clearAuth() {
        this.token = null;
        this.user = null;
        localStorage.removeItem("rbac_token");
        localStorage.removeItem("rbac_user");
    },

    isLoggedIn() {
        return !!this.token;
    },

    hasPermission(perm) {
        if (!this.user || !this.user.permissions) return false;
        return this.user.permissions.includes(perm);
    },

    updateUI() {
        const usernameEl = document.getElementById("currentUsername");
        const rolesEl = document.getElementById("currentRoles");
        if (usernameEl && this.user) {
            usernameEl.textContent = this.user.username;
        }
        if (rolesEl && this.user) {
            const roleNames = (this.user.roles || []).map(r => r.name).join(", ") || "—";
            rolesEl.textContent = `角色: ${roleNames}`;
        }

        document.querySelectorAll("[data-perm]").forEach(el => {
            const perm = el.getAttribute("data-perm");
            el.style.display = this.hasPermission(perm) ? "" : "none";
        });

        document.querySelectorAll(".nav-link[data-page]").forEach(link => {
            if (link.getAttribute("href") === window.location.pathname) {
                link.classList.add("active");
            } else {
                link.classList.remove("active");
            }
        });
    },

    redirectIfNoAuth() {
        if (!this.isLoggedIn()) {
            window.location.href = "/login";
            return false;
        }
        return true;
    }
};

async function apiGet(url) {
    const headers = {};
    if (RBAC.token) headers["Authorization"] = `Bearer ${RBAC.token}`;
    const resp = await fetch(url, { headers });
    if (resp.status === 401) { RBAC.clearAuth(); window.location.href = "/login"; return null; }
    return resp;
}

async function apiPost(url, data, isJson = true) {
    const headers = {};
    if (RBAC.token) headers["Authorization"] = `Bearer ${RBAC.token}`;
    if (isJson) {
        headers["Content-Type"] = "application/json";
        data = JSON.stringify(data);
    } else {
        delete headers["Content-Type"];
    }
    const resp = await fetch(url, { method: "POST", headers, body: data });
    if (resp.status === 401) { RBAC.clearAuth(); window.location.href = "/login"; return null; }
    return resp;
}

async function apiPut(url, data, isJson = true) {
    const headers = {};
    if (RBAC.token) headers["Authorization"] = `Bearer ${RBAC.token}`;
    if (isJson) {
        headers["Content-Type"] = "application/json";
        data = JSON.stringify(data);
    }
    const resp = await fetch(url, { method: "PUT", headers, body: data });
    if (resp.status === 401) { RBAC.clearAuth(); window.location.href = "/login"; return null; }
    return resp;
}

async function apiDelete(url) {
    const headers = {};
    if (RBAC.token) headers["Authorization"] = `Bearer ${RBAC.token}`;
    const resp = await fetch(url, { method: "DELETE", headers });
    if (resp.status === 401) { RBAC.clearAuth(); window.location.href = "/login"; return null; }
    return resp;
}

function logout() {
    RBAC.clearAuth();
    window.location.href = "/login";
}

function formatFileSize(bytes) {
    if (bytes === 0) return "0 B";
    const k = 1024;
    const sizes = ["B", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i];
}

document.addEventListener("DOMContentLoaded", () => {
    RBAC.updateUI();
});
