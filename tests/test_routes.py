import io
import pytest
from app import create_app
from app.models import get_user_by_email

@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    app.config["ENABLE_DEMO_MODE"] = True
    with app.test_client() as client:
        # Pre-authenticate as default demo user for route tests
        with client.session_transaction() as sess:
            sess["user_id"] = 1
            sess["user_email"] = "demo@cloudstorage.com"
            sess["user_name"] = "Demo Cloud Architect"
            sess["demo_mode"] = True
        yield client

@pytest.fixture
def unauthenticated_client():
    app = create_app()
    app.config["TESTING"] = True
    app.config["ENABLE_DEMO_MODE"] = True
    with app.test_client() as client:
        yield client

def test_home_page(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Enterprise AWS S3 Management" in response.data

def test_docs_page(client):
    response = client.get("/docs")
    assert response.status_code == 200
    assert b"Documentation" in response.data

def test_unauthenticated_redirect(unauthenticated_client):
    response = unauthenticated_client.get("/explorer")
    assert response.status_code == 302
    assert "/auth/login" in response.headers["Location"]

def test_unauthenticated_api_blocked(unauthenticated_client):
    response = unauthenticated_client.post("/api/presigned-url", json={
        "bucket": "test",
        "key": "test.txt"
    })
    assert response.status_code == 401
    assert response.get_json()["success"] is False

def test_signup_flow(unauthenticated_client):
    # Test Signup GET
    res_get = unauthenticated_client.get("/auth/signup")
    assert res_get.status_code == 200
    assert b"Get Started" in res_get.data

    # Test Signup POST
    unique_email = "newuser_test@cloudstorage.com"
    res_post = unauthenticated_client.post("/auth/signup", data={
        "full_name": "Test User",
        "email": unique_email,
        "password": "securepassword123",
        "confirm_password": "securepassword123"
    }, follow_redirects=True)
    assert res_post.status_code == 200
    
    # Verify user in database
    user = get_user_by_email(unique_email)
    assert user is not None
    assert user["full_name"] == "Test User"

def test_login_and_logout_flow(unauthenticated_client):
    # Test Login GET
    res_get = unauthenticated_client.get("/auth/login")
    assert res_get.status_code == 200
    assert b"Welcome Back" in res_get.data

    # Test Login POST with demo account
    res_post = unauthenticated_client.post("/auth/login", data={
        "email": "demo@cloudstorage.com",
        "password": "demo1234"
    }, follow_redirects=True)
    assert res_post.status_code == 200
    assert b"Signed in successfully" in res_post.data

    # Test Logout
    res_logout = unauthenticated_client.get("/auth/logout", follow_redirects=True)
    assert res_logout.status_code == 200
    assert b"signed out" in res_logout.data

def test_login_invalid_password(unauthenticated_client):
    res_post = unauthenticated_client.post("/auth/login", data={
        "email": "demo@cloudstorage.com",
        "password": "wrongpassword"
    })
    assert res_post.status_code == 200
    assert b"Invalid email or password" in res_post.data

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
