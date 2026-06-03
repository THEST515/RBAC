"""Tests for file operations: upload, download, delete, security checks."""
import io


class TestListFiles:
    def test_admin_can_list_files_empty(self, client, auth_header):
        resp = client.get("/api/files", headers=auth_header)
        assert resp.status_code == 200
        assert resp.get_json() == []

    def test_viewer_cannot_list_files_without_perm(self, client, viewer_header):
        resp = client.get("/api/files", headers=viewer_header)
        assert resp.status_code == 200
        assert resp.get_json() == []

    def test_unauthenticated_cannot_list_files(self, client):
        resp = client.get("/api/files")
        assert resp.status_code == 401


class TestUploadFile:
    def test_admin_can_upload_txt(self, client, auth_header):
        data = {"file": (io.BytesIO(b"Hello RBAC"), "test.txt")}
        resp = client.post("/api/files", headers=auth_header,
                           content_type="multipart/form-data", data=data)
        assert resp.status_code == 201
        result = resp.get_json()
        assert result["original_filename"] == "test.txt"
        assert result["size"] == 10
        assert result["mime_type"] == "text/plain"

    def test_upload_without_file_rejected(self, client, auth_header):
        resp = client.post("/api/files", headers=auth_header,
                           content_type="multipart/form-data", data={})
        assert resp.status_code == 400

    def test_upload_blocked_extension(self, client, auth_header):
        data = {"file": (io.BytesIO(b"print('hack')"), "malicious.py")}
        resp = client.post("/api/files", headers=auth_header,
                           content_type="multipart/form-data", data=data)
        assert resp.status_code == 400

    def test_upload_blocked_executable(self, client, auth_header):
        data = {"file": (io.BytesIO(b"\x4d\x5a"), "virus.exe")}
        resp = client.post("/api/files", headers=auth_header,
                           content_type="multipart/form-data", data=data)
        assert resp.status_code == 400

    def test_viewer_cannot_upload(self, client, viewer_header):
        data = {"file": (io.BytesIO(b"data"), "viewer_upload.txt")}
        resp = client.post("/api/files", headers=viewer_header,
                           content_type="multipart/form-data", data=data)
        assert resp.status_code == 403


class TestDownloadFile:
    def test_admin_can_download_file(self, client, auth_header):
        data = {"file": (io.BytesIO(b"Download content"), "download_me.txt")}
        upload_resp = client.post("/api/files", headers=auth_header,
                                  content_type="multipart/form-data", data=data)
        file_id = upload_resp.get_json()["id"]

        resp = client.get(f"/api/files/{file_id}", headers=auth_header)
        assert resp.status_code == 200
        assert resp.data == b"Download content"


class TestUpdateFile:
    def test_admin_can_replace_file(self, client, auth_header):
        data = {"file": (io.BytesIO(b"v1"), "replace_me.txt")}
        upload_resp = client.post("/api/files", headers=auth_header,
                                  content_type="multipart/form-data", data=data)
        file_id = upload_resp.get_json()["id"]

        new_data = {"file": (io.BytesIO(b"v2 - replaced"), "replace_me.txt")}
        resp = client.put(f"/api/files/{file_id}", headers=auth_header,
                          content_type="multipart/form-data", data=new_data)
        assert resp.status_code == 200

        download_resp = client.get(f"/api/files/{file_id}", headers=auth_header)
        assert download_resp.data == b"v2 - replaced"


class TestDeleteFile:
    def test_admin_can_delete_file(self, client, auth_header):
        data = {"file": (io.BytesIO(b"to delete"), "delete_me.txt")}
        upload_resp = client.post("/api/files", headers=auth_header,
                                  content_type="multipart/form-data", data=data)
        file_id = upload_resp.get_json()["id"]

        resp = client.delete(f"/api/files/{file_id}", headers=auth_header)
        assert resp.status_code == 200

        info_resp = client.get(f"/api/files/{file_id}/info", headers=auth_header)
        assert info_resp.status_code == 404

    def test_viewer_cannot_delete_file(self, client, auth_header, viewer_header):
        data = {"file": (io.BytesIO(b"protected"), "protected.txt")}
        upload_resp = client.post("/api/files", headers=auth_header,
                                  content_type="multipart/form-data", data=data)
        file_id = upload_resp.get_json()["id"]

        resp = client.delete(f"/api/files/{file_id}", headers=viewer_header)
        assert resp.status_code == 403
