import io
import pytest
from app.s3_service import S3Service

@pytest.fixture
def s3_service():
    """Initializes S3Service in demo/mock mode."""
    return S3Service(is_demo=True, region="us-east-1")

def test_connection(s3_service):
    ok, msg = s3_service.test_connection()
    assert ok is True
    assert "Successfully" in msg

def test_list_buckets(s3_service):
    buckets, err = s3_service.list_buckets()
    assert err is None
    assert len(buckets) > 0
    bucket_names = [b["name"] for b in buckets]
    assert "my-cloud-storage-demo" in bucket_names

def test_create_bucket(s3_service):
    new_bucket = "test-new-unique-bucket"
    ok, err = s3_service.create_bucket(new_bucket)
    assert ok is True
    assert err is None

    buckets, _ = s3_service.list_buckets()
    bucket_names = [b["name"] for b in buckets]
    assert new_bucket in bucket_names

def test_upload_and_download_file(s3_service):
    bucket = "my-cloud-storage-demo"
    key = "unit-tests/sample-test.txt"
    content = b"Hello from automated unit test!"
    
    # Upload
    file_obj = io.BytesIO(content)
    ok, err = s3_service.upload_file(bucket, key, file_obj, content_type="text/plain")
    assert ok is True
    assert err is None

    # Download
    body, ctype, length, err = s3_service.download_file(bucket, key)
    assert err is None
    assert body.read() == content
    assert length == len(content)

def test_list_objects_and_folders(s3_service):
    bucket = "my-cloud-storage-demo"
    
    # List root
    data, err = s3_service.list_objects(bucket, prefix="")
    assert err is None
    assert "folders" in data
    assert "files" in data
    
    folder_names = [f["name"] for f in data["folders"]]
    assert "docs" in folder_names or "images" in folder_names

def test_get_object_metadata(s3_service):
    bucket = "my-cloud-storage-demo"
    key = "welcome.txt"
    
    meta, err = s3_service.get_object_metadata(bucket, key)
    assert err is None
    assert meta is not None
    assert meta["key"] == key
    assert meta["bucket"] == bucket
    assert meta["content_length"] > 0

def test_generate_presigned_url(s3_service):
    bucket = "my-cloud-storage-demo"
    key = "welcome.txt"
    
    url, err = s3_service.generate_presigned_url(bucket, key, expiration=1800)
    assert err is None
    assert url is not None
    assert "X-Amz-Signature" in url or "AWSAccessKeyId" in url or "X-Amz-Algorithm" in url
    assert "welcome.txt" in url

def test_create_folder(s3_service):
    bucket = "my-cloud-storage-demo"
    ok, err = s3_service.create_folder(bucket, prefix="", folder_name="new-test-dir")
    assert ok is True
    assert err is None

    data, _ = s3_service.list_objects(bucket, prefix="")
    folder_names = [f["name"] for f in data["folders"]]
    assert "new-test-dir" in folder_names

def test_delete_object(s3_service):
    bucket = "my-cloud-storage-demo"
    key = "to-be-deleted.txt"
    
    # Create object
    s3_service.upload_file(bucket, key, io.BytesIO(b"delete me"))
    
    # Delete object
    ok, err = s3_service.delete_object(bucket, key)
    assert ok is True
    assert err is None
