import io
import pytest
from app import create_app

@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    app.config["ENABLE_DEMO_MODE"] = True
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess["demo_mode"] = True
        yield client

def test_explorer_get(client):
    response = client.get("/explorer")
    assert response.status_code in (200, 302)

def test_api_upload_file(client):
    data = {
        "bucket": "my-cloud-storage-demo",
        "prefix": "test-uploads",
        "file": (io.BytesIO(b"Flask route test content"), "route-test.txt")
    }
    response = client.post("/api/upload", data=data, content_type="multipart/form-data")
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data["success"] is True

def test_api_presigned_url(client):
    response = client.post("/api/presigned-url", json={
        "bucket": "my-cloud-storage-demo",
        "key": "welcome.txt",
        "expiration": 3600
    })
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data["success"] is True
    assert "url" in json_data
    assert "expires_at" in json_data

def test_api_metadata(client):
    response = client.get("/api/metadata?bucket=my-cloud-storage-demo&key=welcome.txt")
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data["success"] is True
    assert json_data["data"]["key"] == "welcome.txt"

def test_api_create_folder(client):
    response = client.post("/api/create-folder", json={
        "bucket": "my-cloud-storage-demo",
        "prefix": "",
        "folder_name": "api-created-folder"
    })
    assert response.status_code == 200
    assert response.get_json()["success"] is True

def test_api_delete_object(client):
    # First upload
    client.post("/api/upload", data={
        "bucket": "my-cloud-storage-demo",
        "prefix": "",
        "file": (io.BytesIO(b"to delete"), "temp-del.txt")
    }, content_type="multipart/form-data")

    # Delete
    response = client.post("/api/delete", json={
        "bucket": "my-cloud-storage-demo",
        "key": "temp-del.txt"
    })
    assert response.status_code == 200
    assert response.get_json()["success"] is True

def test_settings_page(client):
    response = client.get("/auth/settings")
    assert response.status_code == 200
    assert b"AWS IAM Access Key Controls" in response.data
