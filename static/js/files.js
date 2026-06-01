let selectedFile = null;

document.addEventListener("DOMContentLoaded", () => {
    if (!RBAC.redirectIfNoAuth()) return;
    loadFiles();
    setupDragDrop();
});

function setupDragDrop() {
    const zone = document.getElementById("uploadZone");
    if (!zone) return;

    zone.addEventListener("dragover", (e) => {
        e.preventDefault();
        zone.classList.add("dragover");
    });
    zone.addEventListener("dragleave", () => zone.classList.remove("dragover"));
    zone.addEventListener("drop", (e) => {
        e.preventDefault();
        zone.classList.remove("dragover");
        if (e.dataTransfer.files.length > 0) {
            handleFile(e.dataTransfer.files[0]);
        }
    });
}

function handleFileSelect(input) {
    if (input.files.length > 0) handleFile(input.files[0]);
}

function handleFile(file) {
    selectedFile = file;
    document.getElementById("selectedFile").classList.remove("d-none");
    document.getElementById("selectedFileName").textContent = file.name;
    document.getElementById("selectedFileSize").textContent = ` (${formatFileSize(file.size)})`;
    document.getElementById("uploadBtn").disabled = false;
    document.getElementById("uploadError").classList.add("d-none");
}

async function uploadFile() {
    if (!selectedFile) return;

    const errorEl = document.getElementById("uploadError");
    const progressBar = document.getElementById("uploadProgress");
    const bar = progressBar.querySelector(".progress-bar");

    progressBar.classList.remove("d-none");
    bar.style.width = "30%";

    const formData = new FormData();
    formData.append("file", selectedFile);

    try {
        const resp = await apiPost("/api/files", formData, false);
        if (!resp) return;
        const data = await resp.json();
        if (!resp.ok) {
            errorEl.textContent = data.error || "上传失败";
            errorEl.classList.remove("d-none");
            bar.style.width = "0%";
            progressBar.classList.add("d-none");
            return;
        }
        bar.style.width = "100%";
        setTimeout(() => {
            bootstrap.Modal.getInstance(document.getElementById("uploadModal")).hide();
            selectedFile = null;
            document.getElementById("fileInput").value = "";
            document.getElementById("selectedFile").classList.add("d-none");
            document.getElementById("uploadBtn").disabled = true;
            bar.style.width = "0%";
            progressBar.classList.add("d-none");
            loadFiles();
        }, 500);
    } catch (e) {
        errorEl.textContent = "网络错误";
        errorEl.classList.remove("d-none");
    }
}

async function loadFiles() {
    const loading = document.getElementById("filesLoading");
    const container = document.getElementById("filesTableContainer");
    const empty = document.getElementById("filesEmpty");
    const tbody = document.getElementById("filesTableBody");

    try {
        const resp = await apiGet("/api/files");
        if (!resp || !resp.ok) return;
        const files = await resp.json();

        if (files.length === 0) {
            loading.classList.add("d-none");
            empty.classList.remove("d-none");
            return;
        }

        tbody.innerHTML = files.map(f => `
            <tr class="file-row">
                <td><i class="bi bi-file-earmark me-2"></i><strong>${escapeHtml(f.original_filename)}</strong></td>
                <td>${formatFileSize(f.size)}</td>
                <td><span class="badge bg-light text-dark">${f.mime_type || "—"}</span></td>
                <td>${escapeHtml(f.owner_name)}</td>
                <td>${new Date(f.created_at).toLocaleString("zh-CN")}</td>
                <td>
                    <button class="btn btn-sm btn-outline-success me-1" onclick="downloadFile(${f.id}, '${escapeHtml(f.original_filename)}')" title="下载">
                        <i class="bi bi-download"></i>
                    </button>
                    ${RBAC.hasPermission("file:update") ? `<button class="btn btn-sm btn-outline-primary me-1" onclick="triggerReplace(${f.id})" title="替换">
                        <i class="bi bi-arrow-repeat"></i></button>` : ""}
                    ${RBAC.hasPermission("file:delete") ? `<button class="btn btn-sm btn-outline-danger" onclick="deleteFile(${f.id}, '${escapeHtml(f.original_filename)}')" title="删除">
                        <i class="bi bi-trash"></i></button>` : ""}
                </td>
            </tr>
        `).join("");

        loading.classList.add("d-none");
        container.classList.remove("d-none");
        empty.classList.add("d-none");
    } catch (e) { console.error(e); }
}

function downloadFile(id, filename) {
    const a = document.createElement("a");
    a.href = `/api/files/${id}`;
    a.download = filename;
    const headers = {};
    if (RBAC.token) headers["Authorization"] = `Bearer ${RBAC.token}`;
    fetch(`/api/files/${id}`, { headers })
        .then(r => {
            if (r.status === 401) { RBAC.clearAuth(); window.location.href = "/login"; return; }
            return r.blob();
        })
        .then(blob => {
            if (!blob) return;
            const url = URL.createObjectURL(blob);
            a.href = url;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        })
        .catch(e => console.error(e));
}

function triggerReplace(id) {
    const input = document.createElement("input");
    input.type = "file";
    input.onchange = async function() {
        if (!this.files.length) return;
        const formData = new FormData();
        formData.append("file", this.files[0]);
        try {
            const resp = await apiPut(`/api/files/${id}`, formData, false);
            if (!resp) return;
            const data = await resp.json();
            if (!resp.ok) { alert(data.error || "替换失败"); return; }
            loadFiles();
        } catch (e) { console.error(e); }
    };
    input.click();
}

async function deleteFile(id, filename) {
    if (!confirm(`确定要删除文件 "${filename}" 吗？`)) return;
    try {
        const resp = await apiDelete(`/api/files/${id}`);
        if (!resp) return;
        const data = await resp.json();
        if (!resp.ok) { alert(data.error); return; }
        loadFiles();
    } catch (e) { console.error(e); }
}

function escapeHtml(text) {
    const d = document.createElement("div");
    d.textContent = text;
    return d.innerHTML;
}
