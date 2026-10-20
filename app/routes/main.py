from flask import Blueprint, render_template, request, redirect, url_for, flash, Response, abort
from app import get_s3_service_for_session
import os

main_bp = Blueprint("main", __name__)

def build_breadcrumbs(bucket, prefix):
    breadcrumbs = [{"name": "Buckets", "url": url_for("main.explorer")}]
    if not bucket:
        return breadcrumbs

    breadcrumbs.append({"name": bucket, "url": url_for("main.explorer", bucket=bucket)})
    
    parts = [p for p in prefix.strip("/").split("/") if p]
    accumulated = ""
    for part in parts:
        accumulated += part + "/"
        breadcrumbs.append({
            "name": part,
            "url": url_for("main.explorer", bucket=bucket, prefix=accumulated)
        })
    return breadcrumbs

@main_bp.route("/")
def index():
    return redirect(url_for("main.explorer"))

@main_bp.route("/explorer")
def explorer():
    s3 = get_s3_service_for_session()
    buckets, err = s3.list_buckets()
    
    current_bucket = request.args.get("bucket", "")
    prefix = request.args.get("prefix", "")
    
    if not current_bucket and buckets:
        # Default to first bucket
        current_bucket = buckets[0]["name"]
        return redirect(url_for("main.explorer", bucket=current_bucket))

    folders = []
    files = []
    object_err = None

    if current_bucket:
        obj_data, object_err = s3.list_objects(current_bucket, prefix=prefix)
        folders = obj_data.get("folders", [])
        files = obj_data.get("files", [])

    breadcrumbs = build_breadcrumbs(current_bucket, prefix)

    return render_template(
        "explorer.html",
        buckets=buckets,
        current_bucket=current_bucket,
        prefix=prefix,
        folders=folders,
        files=files,
        breadcrumbs=breadcrumbs,
        bucket_err=err,
        object_err=object_err
    )

@main_bp.route("/download")
def download():
    bucket = request.args.get("bucket")
    key = request.args.get("key")
    if not bucket or not key:
        flash("Bucket and key parameters are required.", "danger")
        return redirect(url_for("main.explorer"))

    s3 = get_s3_service_for_session()
    body, content_type, length, err = s3.download_file(bucket, key)
    if err or not body:
        flash(f"Download failed: {err}", "danger")
        return redirect(url_for("main.explorer", bucket=bucket))

    filename = os.path.basename(key)
    return Response(
        body.read(),
        mimetype=content_type or "application/octet-stream",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Length": str(length) if length else ""
        }
    )

@main_bp.route("/view")
def view_inline():
    bucket = request.args.get("bucket")
    key = request.args.get("key")
    if not bucket or not key:
        abort(400)

    s3 = get_s3_service_for_session()
    body, content_type, length, err = s3.download_file(bucket, key)
    if err or not body:
        abort(404)

    return Response(
        body.read(),
        mimetype=content_type or "text/plain",
        headers={"Content-Disposition": "inline"}
    )
