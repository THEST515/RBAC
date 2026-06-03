let allRoles = [];

document.addEventListener("DOMContentLoaded", async () => {
    if (!RBAC.redirectIfNoAuth()) return;
    await loadRoles();
    await loadUsers();
});

async function loadRoles() {
    try {
        const resp = await apiGet("/api/roles");
        if (resp && resp.ok) allRoles = await resp.json();
    } catch (e) { console.error(e); }
}

async function loadUsers() {
    const loading = document.getElementById("usersLoading");
    const container = document.getElementById("usersTableContainer");
    const tbody = document.getElementById("usersTableBody");

    try {
        const resp = await apiGet("/api/users");
        if (!resp || !resp.ok) return;
        const users = await resp.json();

        tbody.innerHTML = users.map(u => `
            <tr>
                <td>${u.id}</td>
                <td><strong>${escapeHtml(u.username)}</strong></td>
                <td>${escapeHtml(u.email || "—")}</td>
                <td>${(u.roles || []).map(r => `<span class="badge bg-primary me-1">${T.role(r.name)}</span>`).join("") || "—"}</td>
                <td>${u.is_active ? '<span class="badge bg-success">激活</span>' : '<span class="badge bg-secondary">禁用</span>'}</td>
                <td>${new Date(u.created_at).toLocaleString("zh-CN")}</td>
                <td>
                    ${RBAC.hasPermission("user:update") ? `<button class="btn btn-sm btn-outline-primary me-1" onclick="editUser(${u.id})"><i class="bi bi-pencil"></i></button>` : ""}
                    ${RBAC.hasPermission("user:delete") && u.username !== "admin" ? `<button class="btn btn-sm btn-outline-danger" onclick="deleteUser(${u.id}, '${u.username}')"><i class="bi bi-trash"></i></button>` : ""}
                </td>
            </tr>
        `).join("");

        loading.classList.add("d-none");
        container.classList.remove("d-none");
    } catch (e) {
        loading.innerHTML = "<p class='text-danger'>加载失败</p>";
    }
}

async function editUser(id) {
    try {
        const resp = await apiGet(`/api/users/${id}`);
        if (!resp || !resp.ok) return;
        const u = await resp.json();

        document.getElementById("userId").value = u.id;
        document.getElementById("editUsername").value = u.username;
        document.getElementById("editEmail").value = u.email || "";
        document.getElementById("editPassword").value = "";
        document.getElementById("passwordHint").textContent = "(留空则不修改)";
        document.getElementById("editIsActive").checked = u.is_active;
        document.getElementById("userModalTitle").textContent = "编辑用户";

        const rolesDiv = document.getElementById("editRoles");
        const userRoleIds = (u.roles || []).map(r => r.id);
        rolesDiv.innerHTML = allRoles.map(r => `
            <div class="form-check form-check-inline">
                <input class="form-check-input role-check" type="checkbox" value="${r.id}" id="role${r.id}" ${userRoleIds.includes(r.id) ? "checked" : ""}>
                <label class="form-check-label" for="role${r.id}">${T.role(r.name)}</label>
            </div>
        `).join("");

        new bootstrap.Modal(document.getElementById("userModal")).show();
    } catch (e) { console.error(e); }
}

function resetUserForm() {
    document.getElementById("userId").value = "";
    document.getElementById("editUsername").value = "";
    document.getElementById("editEmail").value = "";
    document.getElementById("editPassword").value = "";
    document.getElementById("passwordHint").textContent = "(新建用户必填)";
    document.getElementById("editIsActive").checked = true;
    document.getElementById("userModalTitle").textContent = "添加用户";
    const rolesDiv = document.getElementById("editRoles");
    const viewerRole = allRoles.find(r => r.name === "Viewer");
    rolesDiv.innerHTML = allRoles.map(r => `
        <div class="form-check form-check-inline">
            <input class="form-check-input role-check" type="checkbox" value="${r.id}" id="role${r.id}" ${r.name === "Viewer" ? "checked" : ""}>
            <label class="form-check-label" for="role${r.id}">${r.name}</label>
        </div>
    `).join("");
    document.getElementById("userModalError").classList.add("d-none");
}

async function saveUser() {
    const userId = document.getElementById("userId").value;
    const username = document.getElementById("editUsername").value.trim();
    const email = document.getElementById("editEmail").value.trim();
    const password = document.getElementById("editPassword").value;
    const isActive = document.getElementById("editIsActive").checked;
    const roleIds = Array.from(document.querySelectorAll(".role-check:checked")).map(cb => parseInt(cb.value));
    const errorEl = document.getElementById("userModalError");

    errorEl.classList.add("d-none");

    const payload = {
        username,
        email: email || null,
        is_active: isActive,
        role_ids: roleIds,
    };
    if (password) payload.password = password;

    try {
        let resp;
        if (userId) {
            resp = await apiPut(`/api/users/${userId}`, payload);
        } else {
            resp = await apiPost("/api/users", payload);
        }
        if (!resp) return;
        const data = await resp.json();
        if (!resp.ok) {
            errorEl.textContent = data.error || "操作失败";
            errorEl.classList.remove("d-none");
            return;
        }
        bootstrap.Modal.getInstance(document.getElementById("userModal")).hide();
        await loadUsers();
    } catch (e) {
        errorEl.textContent = "网络错误";
        errorEl.classList.remove("d-none");
    }
}

async function deleteUser(id, username) {
    if (!confirm(`确定要删除用户 "${username}" 吗？此操作不可撤销。`)) return;
    try {
        const resp = await apiDelete(`/api/users/${id}`);
        if (!resp) return;
        const data = await resp.json();
        if (!resp.ok) {
            alert(data.error || "删除失败");
            return;
        }
        await loadUsers();
    } catch (e) { console.error(e); }
}

function escapeHtml(text) {
    const d = document.createElement("div");
    d.textContent = text;
    return d.innerHTML;
}
