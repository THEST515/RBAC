document.addEventListener("DOMContentLoaded", async () => {
    if (!RBAC.redirectIfNoAuth()) return;

    try {
        const [usersResp, rolesResp, filesResp, logsResp] = await Promise.all([
            RBAC.hasPermission("user:read") ? apiGet("/api/users") : null,
            RBAC.hasPermission("role:read") ? apiGet("/api/roles") : null,
            RBAC.hasPermission("file:read") ? apiGet("/api/files") : null,
            RBAC.hasPermission("audit:read") ? apiGet("/api/audit-logs?per_page=5") : null,
        ]);

        if (usersResp && usersResp.ok) {
            const users = await usersResp.json();
            document.getElementById("statUsers").textContent = users.length;
        }

        if (rolesResp && rolesResp.ok) {
            const roles = await rolesResp.json();
            document.getElementById("statRoles").textContent = roles.length;
        }

        if (filesResp && filesResp.ok) {
            const files = await filesResp.json();
            document.getElementById("statFiles").textContent = files.length;
        }

        if (logsResp && logsResp.ok) {
            const logs = await logsResp.json();
            document.getElementById("statLogs").textContent = logs.total || 0;

            const recentEl = document.getElementById("recentLogs");
            if (logs.items && logs.items.length > 0) {
                recentEl.innerHTML = `
                    <table class="table table-sm">
                        <thead><tr><th>时间</th><th>用户</th><th>操作</th><th>详情</th></tr></thead>
                        <tbody>
                            ${logs.items.map(l => `
                                <tr>
                                    <td>${new Date(l.timestamp).toLocaleString("zh-CN")}</td>
                                    <td>${l.username || "—"}</td>
                                    <td><span class="badge bg-secondary">${T.perm(l.action) || l.action}</span></td>
                                    <td class="audit-log-detail">${l.details || "—"}</td>
                                </tr>
                            `).join("")}
                        </tbody>
                    </table>`;
            } else {
                recentEl.innerHTML = "<p class='text-muted'>暂无操作记录</p>";
            }
        } else {
            document.getElementById("statLogs").textContent = "—";
        }
    } catch (err) {
        console.error("仪表盘加载错误:", err);
    }
});
