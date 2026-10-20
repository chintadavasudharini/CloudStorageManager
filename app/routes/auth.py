from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, current_app
from app.s3_service import S3Service

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/settings", methods=["GET"])
def settings():
    saved_key = session.get("aws_access_key", "")
    saved_region = session.get("aws_region", current_app.config.get("AWS_DEFAULT_REGION", "us-east-1"))
    is_demo = session.get("demo_mode", current_app.config.get("ENABLE_DEMO_MODE", True))
    
    return render_template(
        "settings.html",
        saved_key=saved_key,
        saved_region=saved_region,
        is_demo=is_demo
    )

@auth_bp.route("/save", methods=["POST"])
def save_credentials():
    access_key = request.form.get("aws_access_key", "").strip()
    secret_key = request.form.get("aws_secret_key", "").strip()
    region = request.form.get("aws_region", "us-east-1").strip()
    
    if not access_key or not secret_key:
        flash("AWS Access Key and Secret Key are both required.", "danger")
        return redirect(url_for("auth.settings"))

    # Test the credentials
    tester = S3Service(access_key=access_key, secret_key=secret_key, region=region, is_demo=False)
    ok, msg = tester.test_connection()
    if not ok:
        flash(f"Connection test failed: {msg}", "danger")
        return redirect(url_for("auth.settings"))

    # Save to session
    session["aws_access_key"] = access_key
    session["aws_secret_key"] = secret_key
    session["aws_region"] = region
    session["demo_mode"] = False
    
    flash("AWS Credentials validated and saved for this session successfully!", "success")
    return redirect(url_for("main.explorer"))

@auth_bp.route("/toggle-demo", methods=["POST"])
def toggle_demo():
    enable = request.form.get("enable_demo") == "true"
    session["demo_mode"] = enable
    if enable:
        flash("Switched to Demo Mode (Mock AWS S3 with sample datasets).", "info")
    else:
        flash("Switched to Live AWS Credentials Mode.", "info")
    return redirect(url_for("main.explorer"))

@auth_bp.route("/clear", methods=["POST"])
def clear_credentials():
    session.pop("aws_access_key", None)
    session.pop("aws_secret_key", None)
    session["demo_mode"] = True
    flash("Session credentials cleared. Returned to Demo Mode.", "info")
    return redirect(url_for("auth.settings"))

@auth_bp.route("/test", methods=["POST"])
def test_credentials():
    data = request.get_json() or {}
    access_key = data.get("aws_access_key", "").strip()
    secret_key = data.get("aws_secret_key", "").strip()
    region = data.get("aws_region", "us-east-1").strip()

    if not access_key or not secret_key:
        return jsonify({"success": False, "message": "Both Access Key and Secret Key are required."})

    tester = S3Service(access_key=access_key, secret_key=secret_key, region=region, is_demo=False)
    ok, msg = tester.test_connection()
    return jsonify({"success": ok, "message": msg})
