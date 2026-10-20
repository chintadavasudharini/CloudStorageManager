from flask import Blueprint, request, jsonify, session
from app import get_s3_service_for_session
from datetime import datetime, timedelta, timezone

api_bp = Blueprint("api", __name__)

@api_bp.before_request
def require_api_authentication():
    if not session.get("user_id"):
        return jsonify({"success": False, "error": "Authentication required. Please sign in to perform this action."}), 401

@api_bp.route("/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        return jsonify({"success": False, "error": "No file uploaded"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"success": False, "error": "No selected file"}), 400

    bucket = request.form.get("bucket")
    prefix = request.form.get("prefix", "")
    
    if not bucket:
        return jsonify({"success": False, "error": "Target bucket is required"}), 400

    prefix = prefix.strip("/")
    key = f"{prefix}/{file.filename}" if prefix else file.filename

    s3 = get_s3_service_for_session()
    ok, err = s3.upload_file(
        bucket_name=bucket,
        key=key,
        file_obj=file,
        content_type=file.content_type,
        extra_metadata={"uploaded-via": "CloudStorageManager"}
    )

    if not ok:
        return jsonify({"success": False, "error": err}), 500

    return jsonify({"success": True, "key": key, "message": f"Successfully uploaded '{file.filename}'"})

@api_bp.route("/presigned-url", methods=["POST"])
def presigned_url():
    data = request.get_json() or {}
    bucket = data.get("bucket")
    key = data.get("key")
    
    try:
        expiration = int(data.get("expiration", 3600))
        # Clamp between 1 minute (60s) and 7 days (604800s)
        expiration = max(60, min(expiration, 604800))
    except (ValueError, TypeError):
        expiration = 3600

    http_method = data.get("method", "get_object")

    if not bucket or not key:
        return jsonify({"success": False, "error": "Bucket and Key are required."}), 400

    s3 = get_s3_service_for_session()
    url, err = s3.generate_presigned_url(bucket, key, expiration=expiration, http_method=http_method)

    if err or not url:
        return jsonify({"success": False, "error": err or "Failed to generate presigned URL."}), 500

    expires_at = (datetime.now(timezone.utc) + timedelta(seconds=expiration)).strftime("%Y-%m-%d %H:%M:%S UTC")

    return jsonify({
        "success": True,
        "url": url,
        "expires_in_seconds": expiration,
        "expires_at": expires_at,
        "bucket": bucket,
        "key": key
    })

@api_bp.route("/delete", methods=["POST"])
def delete_object():
    data = request.get_json() or request.form
    bucket = data.get("bucket")
    key = data.get("key")

    if not bucket or not key:
        return jsonify({"success": False, "error": "Bucket and Key are required."}), 400

    s3 = get_s3_service_for_session()
    ok, err = s3.delete_object(bucket, key)
    if not ok:
        return jsonify({"success": False, "error": err}), 500

    return jsonify({"success": True, "message": f"Successfully deleted '{key}'."})

@api_bp.route("/create-bucket", methods=["POST"])
def create_bucket():
    data = request.get_json() or request.form
    bucket_name = data.get("bucket_name", "").strip().lower()
    region = data.get("region", "").strip() or None

    if not bucket_name:
        return jsonify({"success": False, "error": "Bucket name is required."}), 400

    s3 = get_s3_service_for_session()
    ok, err = s3.create_bucket(bucket_name, region=region)
    if not ok:
        return jsonify({"success": False, "error": err}), 400

    return jsonify({"success": True, "bucket_name": bucket_name, "message": f"Bucket '{bucket_name}' created successfully."})

@api_bp.route("/create-folder", methods=["POST"])
def create_folder():
    data = request.get_json() or request.form
    bucket = data.get("bucket")
    prefix = data.get("prefix", "")
    folder_name = data.get("folder_name", "").strip()

    if not bucket or not folder_name:
        return jsonify({"success": False, "error": "Bucket and folder name are required."}), 400

    s3 = get_s3_service_for_session()
    ok, err = s3.create_folder(bucket, prefix, folder_name)
    if not ok:
        return jsonify({"success": False, "error": err}), 500

    return jsonify({"success": True, "message": f"Folder '{folder_name}' created successfully."})

@api_bp.route("/metadata", methods=["GET"])
def get_metadata():
    bucket = request.args.get("bucket")
    key = request.args.get("key")

    if not bucket or not key:
        return jsonify({"success": False, "error": "Bucket and key parameters are required."}), 400

    s3 = get_s3_service_for_session()
    metadata, err = s3.get_object_metadata(bucket, key)
    if err or not metadata:
        return jsonify({"success": False, "error": err or "Object not found."}), 404

    return jsonify({"success": True, "data": metadata})
