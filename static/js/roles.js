let allPermissions = [];

document.addEventListener("DOMContentLoaded", async () => {
    if (!RBAC.redirectIfNoAuth()) return;
    await loadPermissions();
    await loadRoles();
});

async function loadPermissions() {
    try {
        const resp = await apiGet("/api/permissions");
        if (resp && resp.ok) allPermissions = await resp.json();
    } catch (e) { console.error(e); }
}

async function loadRoles() {
    const loading = document.getElementById("rolesLoading");
    const container = document.getElementById("rolesTableContainer");
    const tbody = document.getElementById("rolesTableBody");

    try {
        const resp = await apiGet("/api/roles");
        if (!resp || !resp.ok) return;
        const roles = await resp.json();

        tbody.innerHTML = roles.map(r => `
            <tr>
                <td>${r.id}</td>
                <td><strong>${escapeHtml(r.name)}</strong></td>
                <td>${escapeHtml(r.description || "—")}</td>
                <td><span class="badge bg-info">${(r.permissions || []).length}</span></td>
                <td>${r.user_count}</td>
                <td>
                    <button class="btn btn-sm btn-outline-info me-1" onclick="showPermissionMatrix(${r.id}, '${escapeHtml(r.name)}')" ${!RBAC.hasPermission("role:update") ? "disabled" : ""}>
                        <i class="bi bi-grid-3x3"></i> 权限
                    </button>
                    ${RBAC.hasPermission("role:update") ? `<button class="btn btn-sm btn-outline-primary me-1" onclick="editRole(${r.id})"><i class="bi bi-pencil"></i></button>` : ""}
                    ${RBAC.hasPermission("role:delete") && r.name !== "Admin" && r.name !== "Viewer" ? `<button class="btn btn-sm btn-outline-danger" onclick="deleteRole(${r.id}, '${escapeHtml(r.name)}')"><i class="bi bi-trash"></i></button>` : ""}
                </td>
            </tr>
        `).join("");

        loading.classList.add("d-none");
        container.classList.remove("d-none");
    } catch (e) { console.error(e); }
}

function resetRoleForm() {
    document.getElementById("roleId").value = "";
    document.getElementById("editRoleName").value = "";
    document.getElementById("editRoleDesc").value = "";
    document.getElementById("roleModalTitle").textContent = "添加角色";
    document.getElementById("roleModalError").classList.add("d-none");
}

async function editRole(id) {
    try {
        const resp = await apiGet(`/api/roles/${id}`);
        if (!resp || !resp.ok) return;
        const r = await resp.json();
        document.getElementById("roleId").value = r.id;
        document.getElementById("editRoleName").value = r.name;
        document.getElementById("editRoleDesc").value = r.description || "";
        document.getElementById("roleModalTitle").textContent = "编辑角色";
        new bootstrap.Modal(document.getElementById("roleModal")).show();
    } catch (e) { console.error(e); }
}

async function saveRole() {
    const roleId = document.getElementById("roleId").value;
    const name = document.getElementById("editRoleName").value.trim();
    const description = document.getElementById("editRoleDesc").value.trim();
    const errorEl = document.getElementById("roleModalError");

    errorEl.classList.add("d-none");

    try {
        let resp;
        if (roleId) {
            resp = await apiPut(`/api/roles/${roleId}`, { name, description });
        } else {
            resp = await apiPost("/api/roles", { name, description });
        }
        if (!resp) return;
        const data = await resp.json();
        if (!resp.ok) {
            errorEl.textContent = data.error || "操作失败";
            errorEl.classList.remove("d-none");
            return;
        }
        bootstrap.Modal.getInstance(document.getElementById("roleModal")).hide();
        await loadRoles();
    } catch (e) { console.error(e); }
}

async function deleteRole(id, name) {
    if (!confirm(`确定要删除角色 "${name}" 吗？`)) return;
    try {
        const resp = await apiDelete(`/api/roles/${id}`);
        if (!resp) return;
        const data = await resp.json();
        if (!resp.ok) { alert(data.error); return; }
        await loadRoles();
    } catch (e) { console.error(e); }
}

async function showPermissionMatrix(roleId, roleName) {
    try {
        const resp = await apiGet(`/api/roles/${roleId}/permissions`);
        if (!resp || !resp.ok) return;
        const rolePerms = await resp.json();
        const rolePermNames = rolePerms.map(p => p.name);

        document.getElementById("permMatrixRoleName").textContent = roleName;
        document.getElementById("permMatrixCard").style.display = "block";

        const resources = [...new Set(allPermissions.map(p => p.resource))];
        const actions = [...new Set(allPermissions.map(p => p.action))];

        const resourceNames = { user: "用户", role: "角色", file: "文件", audit: "审计" };
        const actionNames = { create: "创建", read: "读取", update: "更新", delete: "删除" };
        let html = '<table class="table table-bordered permission-matrix"><thead><tr><th>资源 \\ 操作</th>';
        actions.forEach(a => { html += `<th>${actionNames[a] || escapeHtml(a)}</th>`; });
        html += '</tr></thead><tbody>';

        resources.forEach(res => {
            html += `<tr><td><strong>${resourceNames[res] || escapeHtml(res)}</strong></td>`;
            actions.forEach(act => {
                const perm = allPermissions.find(p => p.resource === res && p.action === act);
                if (perm) {
                    const checked = rolePermNames.includes(perm.name) ? "checked" : "";
                    html += `<td><input class="form-check-input perm-check" type="checkbox" value="${perm.id}" data-role="${roleId}" ${checked}></td>`;
                } else {
                    html += '<td></td>';
                }
            });
            html += '</tr>';
        });
        html += '</tbody></table>';
        html += `<button class="btn btn-primary btn-sm" onclick="savePermissions(${roleId})"><i class="bi bi-check-lg"></i> 保存权限</button>`;

        document.getElementById("permMatrixContent").innerHTML = html;
        document.getElementById("permMatrixCard").scrollIntoView({ behavior: "smooth" });
    } catch (e) { console.error(e); }
}

async function savePermissions(roleId) {
    const checked = Array.from(document.querySelectorAll(`.perm-check[data-role="${roleId}"]:checked`))
        .map(cb => parseInt(cb.value));
    try {
        const resp = await apiPut(`/api/roles/${roleId}/permissions`, { permission_ids: checked });
        if (!resp) return;
        if (!resp.ok) { alert("保存失败"); return; }
        alert("权限已更新");
        await loadRoles();
        document.getElementById("permMatrixCard").style.display = "none";
    } catch (e) { console.error(e); }
}

function escapeHtml(text) {
    const d = document.createElement("div");
    d.textContent = text;
    return d.innerHTML;
}
