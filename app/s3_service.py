import boto3
from botocore.exceptions import ClientError, NoCredentialsError, PartialCredentialsError
from botocore.client import Config as BotoConfig
import mimetypes
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Global mock instance for Demo Mode
_moto_server = None
_demo_initialized = False

def init_demo_s3():
    """Initializes a moto mock S3 environment with sample buckets and objects."""
    global _moto_server, _demo_initialized
    if not _demo_initialized:
        try:
            from moto import mock_aws
            mock = mock_aws()
            mock.start()
            
            client = boto3.client(
                "s3",
                region_name="us-east-1",
                aws_access_key_id="demo-access-key",
                aws_secret_access_key="demo-secret-key"
            )
            
            # Create sample buckets
            buckets = ["my-cloud-storage-demo", "company-assets-prod", "secure-documents-vault"]
            for b in buckets:
                client.create_bucket(Bucket=b)
                
            # Add sample files
            sample_files = [
                ("my-cloud-storage-demo", "welcome.txt", b"Welcome to CloudStorageManager!\nA web-based interface for managing AWS S3 buckets.", "text/plain"),
                ("my-cloud-storage-demo", "docs/architecture.md", b"# Cloud Storage Manager Architecture\nFlask backend with Boto3 SDK.", "text/markdown"),
                ("my-cloud-storage-demo", "docs/security-notes.txt", b"Presigned URLs provide secure temporary access without opening S3 bucket permissions.", "text/plain"),
                ("my-cloud-storage-demo", "images/sample-logo.svg", b"<svg xmlns='http://www.w3.org/2000/svg' width='100' height='100'><circle cx='50' cy='50' r='40' fill='#2563eb'/></svg>", "image/svg+xml"),
                ("company-assets-prod", "branding/guidelines.pdf", b"%PDF-1.4 sample pdf content", "application/pdf"),
                ("secure-documents-vault", "confidential/q4-report.csv", b"Category,Amount,Date\nRevenue,150000,2025-10-01", "text/csv"),
            ]
            
            for b_name, key, data, ctype in sample_files:
                client.put_object(
                    Bucket=b_name,
                    Key=key,
                    Body=data,
                    ContentType=ctype,
                    Metadata={"uploaded-by": "CloudStorageManager-Demo"}
                )
            
            _demo_initialized = True
            logger.info("Demo S3 environment successfully initialized with sample data.")
        except Exception as e:
            logger.error(f"Failed to initialize demo S3: {e}")

class S3Service:
    def __init__(self, access_key=None, secret_key=None, region="us-east-1", is_demo=False):
        self.region = region or "us-east-1"
        self.is_demo = is_demo
        self.access_key = access_key
        self.secret_key = secret_key

        if self.is_demo:
            init_demo_s3()
            self.client = boto3.client(
                "s3",
                region_name=self.region,
                aws_access_key_id="demo-access-key",
                aws_secret_access_key="demo-secret-key",
                config=BotoConfig(signature_version="s3v4")
            )
        elif access_key and secret_key:
            self.client = boto3.client(
                "s3",
                region_name=self.region,
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                config=BotoConfig(signature_version="s3v4")
            )
        else:
            # Fallback to default AWS credential chain (env vars, ~/.aws/credentials, IAM role)
            self.client = boto3.client(
                "s3",
                region_name=self.region,
                config=BotoConfig(signature_version="s3v4")
            )

    def test_connection(self):
        """Validates S3 connectivity and credentials."""
        try:
            self.client.list_buckets()
            return True, "Successfully connected to AWS S3"
        except (NoCredentialsError, PartialCredentialsError) as e:
            return False, f"AWS Credentials error: {str(e)}"
        except ClientError as e:
            code = e.response.get("Error", {}).get("Code", "Unknown")
            msg = e.response.get("Error", {}).get("Message", str(e))
            return False, f"AWS Error ({code}): {msg}"
        except Exception as e:
            return False, f"Connection failed: {str(e)}"

    def list_buckets(self):
        """Lists all S3 buckets available for credentials."""
        try:
            response = self.client.list_buckets()
            buckets = []
            for b in response.get("Buckets", []):
                buckets.append({
                    "name": b["Name"],
                    "creation_date": b["CreationDate"].strftime("%Y-%m-%d %H:%M:%S UTC") if isinstance(b["CreationDate"], datetime) else str(b["CreationDate"])
                })
            return buckets, None
        except Exception as e:
            logger.error(f"Error listing buckets: {e}")
            return [], str(e)

    def create_bucket(self, bucket_name, region=None):
        """Creates a new S3 bucket."""
        try:
            target_region = region or self.region
            create_kwargs = {"Bucket": bucket_name}
            
            # LocationConstraint is required for all regions except us-east-1
            if target_region and target_region != "us-east-1":
                create_kwargs["CreateBucketConfiguration"] = {
                    "LocationConstraint": target_region
                }
                
            self.client.create_bucket(**create_kwargs)
            return True, None
        except ClientError as e:
            code = e.response.get("Error", {}).get("Code", "")
            msg = e.response.get("Error", {}).get("Message", str(e))
            return False, f"{code}: {msg}"
        except Exception as e:
            return False, str(e)

    def list_objects(self, bucket_name, prefix=""):
        """
        Lists folders and files under a prefix in a bucket using Delimiter='/'.
        Returns folders (CommonPrefixes) and files (Contents).
        """
        try:
            if prefix and not prefix.endswith("/"):
                prefix += "/"

            paginator = self.client.get_paginator("list_objects_v2")
            pages = paginator.paginate(
                Bucket=bucket_name,
                Prefix=prefix,
                Delimiter="/"
            )

            folders = []
            files = []

            for page in pages:
                # Sub-directories / CommonPrefixes
                for cp in page.get("CommonPrefixes", []):
                    folder_path = cp.get("Prefix")
                    folder_name = folder_path[len(prefix):].rstrip("/")
                    folders.append({
                        "name": folder_name,
                        "prefix": folder_path
                    })

                # Files / Contents
                for obj in page.get("Contents", []):
                    key = obj.get("Key")
                    # Skip the folder marker itself
                    if key == prefix:
                        continue
                    
                    file_name = key[len(prefix):]
                    if not file_name:
                        continue

                    last_modified = obj.get("LastModified")
                    if isinstance(last_modified, datetime):
                        last_mod_str = last_modified.strftime("%Y-%m-%d %H:%M:%S UTC")
                    else:
                        last_mod_str = str(last_modified)

                    files.append({
                        "key": key,
                        "name": file_name,
                        "size": obj.get("Size", 0),
                        "last_modified": last_mod_str,
                        "etag": obj.get("ETag", "").strip('"'),
                        "storage_class": obj.get("StorageClass", "STANDARD")
                    })

            return {"folders": folders, "files": files, "prefix": prefix}, None
        except Exception as e:
            logger.error(f"Error listing objects in {bucket_name}: {e}")
            return {"folders": [], "files": [], "prefix": prefix}, str(e)

    def get_object_metadata(self, bucket_name, key):
        """Retrieves detailed metadata for an S3 object."""
        try:
            response = self.client.head_object(Bucket=bucket_name, Key=key)
            last_modified = response.get("LastModified")
            if isinstance(last_modified, datetime):
                last_mod_str = last_modified.strftime("%Y-%m-%d %H:%M:%S UTC")
            else:
                last_mod_str = str(last_modified)

            return {
                "key": key,
                "bucket": bucket_name,
                "content_length": response.get("ContentLength", 0),
                "content_type": response.get("ContentType", "application/octet-stream"),
                "last_modified": last_mod_str,
                "etag": response.get("ETag", "").strip('"'),
                "storage_class": response.get("StorageClass", "STANDARD"),
                "server_side_encryption": response.get("ServerSideEncryption", "None"),
                "metadata": response.get("Metadata", {}),
                "version_id": response.get("VersionId", "null")
            }, None
        except ClientError as e:
            return None, e.response.get("Error", {}).get("Message", str(e))
        except Exception as e:
            return None, str(e)

    def upload_file(self, bucket_name, key, file_obj, content_type=None, extra_metadata=None):
        """Uploads a file object to S3."""
        try:
            if not content_type:
                content_type, _ = mimetypes.guess_type(key)
                if not content_type:
                    content_type = "application/octet-stream"

            extra_args = {"ContentType": content_type}
            if extra_metadata and isinstance(extra_metadata, dict):
                extra_args["Metadata"] = extra_metadata

            self.client.upload_fileobj(
                Fileobj=file_obj,
                Bucket=bucket_name,
                Key=key,
                ExtraArgs=extra_args
            )
            return True, None
        except Exception as e:
            logger.error(f"Upload error: {e}")
            return False, str(e)

    def download_file(self, bucket_name, key):
        """Retrieves an object body and content type for download."""
        try:
            response = self.client.get_object(Bucket=bucket_name, Key=key)
            return response["Body"], response.get("ContentType", "application/octet-stream"), response.get("ContentLength", 0), None
        except Exception as e:
            return None, None, 0, str(e)

    def delete_object(self, bucket_name, key):
        """Deletes an object from an S3 bucket."""
        try:
            self.client.delete_object(Bucket=bucket_name, Key=key)
            return True, None
        except Exception as e:
            return False, str(e)

    def create_folder(self, bucket_name, prefix, folder_name):
        """Creates a virtual folder by uploading an empty object with a trailing slash."""
        try:
            folder_name = folder_name.strip("/ ")
            if not folder_name:
                return False, "Folder name cannot be empty"
            
            full_key = f"{prefix.rstrip('/')}/{folder_name}/" if prefix.strip("/") else f"{folder_name}/"
            self.client.put_object(Bucket=bucket_name, Key=full_key, Body=b"")
            return True, None
        except Exception as e:
            return False, str(e)

    def generate_presigned_url(self, bucket_name, key, expiration=3600, http_method="get_object"):
        """
        Generates a secure presigned URL with a configurable expiry (in seconds).
        Supports GET (download) and PUT (upload).
        """
        try:
            client_method = "get_object" if http_method == "get_object" else "put_object"
            params = {"Bucket": bucket_name, "Key": key}
            
            url = self.client.generate_presigned_url(
                ClientMethod=client_method,
                Params=params,
                ExpiresIn=expiration
            )
            return url, None
        except ClientError as e:
            return None, e.response.get("Error", {}).get("Message", str(e))
        except Exception as e:
            return None, str(e)
