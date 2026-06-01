let currentPage = 1;
let currentFilters = {};

document.addEventListener("DOMContentLoaded", () => {
    if (!RBAC.redirectIfNoAuth()) return;
    loadLogs();
});

async function loadLogs(page = 1) {
    currentPage = page;
    const loading = document.getElementById("logsLoading");
    const container = document.getElementById("logsTableContainer");
    const tbody = document.getElementById("logsTableBody");
    const pagination = document.getElementById("logsPagination");

    const params = new URLSearchParams();
    params.set("page", page);
    params.set("per_page", 15);
    Object.entries(currentFilters).forEach(([k, v]) => { if (v) params.set(k, v); });

    try {
        const resp = await apiGet(`/api/audit-logs?${params.toString()}`);
        if (!resp || !resp.ok) return;
        const data = await resp.json();

        if (data.items.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted py-4">暂无记录</td></tr>';
        } else {
            tbody.innerHTML = data.items.map(l => `
                <tr>
                    <td class="text-nowrap">${new Date(l.timestamp).toLocaleString("zh-CN")}</td>
                    <td>${escapeHtml(l.username || "—")}</td>
                    <td><span class="badge ${actionBadge(l.action)}">${actionLabel(l.action)}</span></td>
                    <td>${l.resource_type || "—"}${l.resource_id ? ` #${l.resource_id}` : ""}</td>
                    <td class="audit-log-detail" title="${escapeHtml(l.details || "")}">${escapeHtml(l.details || "—")}</td>
                    <td><small>${l.ip_address || "—"}</small></td>
                </tr>
            `).join("");
        }

        pagination.innerHTML = buildPagination(data.page, data.pages);

        loading.classList.add("d-none");
        container.classList.remove("d-none");
    } catch (e) { console.error(e); }
}

function actionLabel(action) {
    const map = {
        "LOGIN_SUCCESS": "登录成功",
        "LOGIN_FAILED": "登录失败",
        "USER_REGISTER": "用户注册",
        "USER_CREATED": "用户创建",
        "USER_UPDATED": "用户更新",
        "USER_DELETED": "用户删除",
        "ROLE_CREATED": "角色创建",
        "ROLE_UPDATED": "角色更新",
        "ROLE_DELETED": "角色删除",
        "ROLE_PERMISSIONS_CHANGED": "权限变更",
        "FILE_UPLOAD": "文件上传",
        "FILE_DOWNLOAD": "文件下载",
        "FILE_UPDATED": "文件更新",
        "FILE_DELETED": "文件删除",
        "PERMISSION_DENIED": "权限拒绝",
    };
    return map[action] || action;
}

function actionBadge(action) {
    if (action.includes("DENIED") || action.includes("FAILED")) return "bg-danger";
    if (action.includes("DELETE")) return "bg-danger";
    if (action.includes("CREATE") || action.includes("UPLOAD") || action.includes("REGISTER")) return "bg-success";
    if (action.includes("UPDATE")) return "bg-warning text-dark";
    if (action.includes("LOGIN")) return "bg-info";
    return "bg-secondary";
}

function buildPagination(page, pages) {
    if (pages <= 1) return "";
    let html = '<ul class="pagination pagination-sm justify-content-center">';
    html += `<li class="page-item ${page <= 1 ? "disabled" : ""}"><a class="page-link" href="#" onclick="loadLogs(${page - 1})">&laquo;</a></li>`;
    for (let i = 1; i <= pages; i++) {
        html += `<li class="page-item ${i === page ? "active" : ""}"><a class="page-link" href="#" onclick="loadLogs(${i})">${i}</a></li>`;
    }
    html += `<li class="page-item ${page >= pages ? "disabled" : ""}"><a class="page-link" href="#" onclick="loadLogs(${page + 1})">&raquo;</a></li>`;
    html += '</ul>';
    return html;
}

function applyFilter() {
    const action = document.getElementById("filterAction").value;
    const resource = document.getElementById("filterResource").value;
    const startDate = document.getElementById("filterStartDate").value;
    const endDate = document.getElementById("filterEndDate").value;

    currentFilters = {};
    if (action) currentFilters.action = action;
    if (resource) currentFilters.resource_type = resource;
    if (startDate) currentFilters.start_date = startDate;
    if (endDate) currentFilters.end_date = endDate;

    loadLogs(1);
}

function resetFilter() {
    document.getElementById("filterAction").value = "";
    document.getElementById("filterResource").value = "";
    document.getElementById("filterStartDate").value = "";
    document.getElementById("filterEndDate").value = "";
    currentFilters = {};
    loadLogs(1);
}

function escapeHtml(text) {
    const d = document.createElement("div");
    d.textContent = text;
    return d.innerHTML;
}
