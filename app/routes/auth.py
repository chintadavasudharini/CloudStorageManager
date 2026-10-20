from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, current_app
from app.s3_service import S3Service
from app.models import create_user, get_user_by_email, get_user_by_id, check_user_password, update_user_aws_creds
from app.auth_utils import login_required
import re

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/signup", methods=["GET", "POST"])
def signup():
    if session.get("user_id"):
        return redirect(url_for("main.explorer"))

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        # Validation
        if not full_name or not email or not password:
            flash("All fields are required.", "danger")
            return render_template("signup.html", full_name=full_name, email=email)

        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            flash("Please enter a valid email address.", "danger")
            return render_template("signup.html", full_name=full_name, email=email)

        if len(password) < 6:
            flash("Password must be at least 6 characters long.", "danger")
            return render_template("signup.html", full_name=full_name, email=email)

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template("signup.html", full_name=full_name, email=email)

        user, err = create_user(email, full_name, password)
        if err:
            flash(err, "danger")
            return render_template("signup.html", full_name=full_name, email=email)

        # Successful registration - log in automatically
        session["user_id"] = user["id"]
        session["user_email"] = user["email"]
        session["user_name"] = user["full_name"]
        session["demo_mode"] = True

        flash(f"Account created successfully! Welcome to CloudStorageManager, {full_name}.", "success")
        next_page = request.args.get("next")
        return redirect(next_page or url_for("main.explorer"))

    return render_template("signup.html")

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect(url_for("main.explorer"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        remember = request.form.get("remember") == "on"

        if not email or not password:
            flash("Please enter both email and password.", "danger")
            return render_template("login.html", email=email)

        user = get_user_by_email(email)
        if not user or not check_user_password(user, password):
            flash("Invalid email or password. Please try again.", "danger")
            return render_template("login.html", email=email)

        # Establish session
        session["user_id"] = user["id"]
        session["user_email"] = user["email"]
        session["user_name"] = user["full_name"]

        # Restore saved AWS credentials if any
        if user.get("aws_access_key") and user.get("aws_secret_key"):
            session["aws_access_key"] = user["aws_access_key"]
            session["aws_secret_key"] = user["aws_secret_key"]
            session["aws_region"] = user.get("aws_region") or "us-east-1"
            session["demo_mode"] = False
        else:
            session["demo_mode"] = True

        flash(f"Signed in successfully as {user['full_name']}.", "success")
        next_page = request.args.get("next")
        return redirect(next_page or url_for("main.explorer"))

    return render_template("login.html")

@auth_bp.route("/logout")
def logout():
    user_name = session.get("user_name", "User")
    session.pop("user_id", None)
    session.pop("user_email", None)
    session.pop("user_name", None)
    session.pop("aws_access_key", None)
    session.pop("aws_secret_key", None)
    flash(f"You have been signed out. See you soon!", "info")
    return redirect(url_for("auth.login"))

@auth_bp.route("/settings", methods=["GET"])
@login_required
def settings():
    user = get_user_by_id(session.get("user_id"))
    saved_key = session.get("aws_access_key") or (user.get("aws_access_key") if user else "")
    saved_region = session.get("aws_region") or (user.get("aws_region") if user else current_app.config.get("AWS_DEFAULT_REGION", "us-east-1"))
    is_demo = session.get("demo_mode", current_app.config.get("ENABLE_DEMO_MODE", True))
    
    return render_template(
        "settings.html",
        saved_key=saved_key,
        saved_region=saved_region,
        is_demo=is_demo
    )

@auth_bp.route("/save", methods=["POST"])
@login_required
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

    # Persist to database profile
    user_id = session.get("user_id")
    if user_id:
        update_user_aws_creds(user_id, access_key, secret_key, region)
    
    flash("AWS Credentials validated and saved to your account successfully!", "success")
    return redirect(url_for("main.explorer"))

@auth_bp.route("/toggle-demo", methods=["POST"])
@login_required
def toggle_demo():
    enable = request.form.get("enable_demo") == "true"
    session["demo_mode"] = enable
    if enable:
        flash("Switched to Demo Mode (Mock AWS S3 with sample datasets).", "info")
    else:
        flash("Switched to Live AWS Credentials Mode.", "info")
    return redirect(url_for("main.explorer"))

@auth_bp.route("/clear", methods=["POST"])
@login_required
def clear_credentials():
    session.pop("aws_access_key", None)
    session.pop("aws_secret_key", None)
    session["demo_mode"] = True

    user_id = session.get("user_id")
    if user_id:
        update_user_aws_creds(user_id, "", "", "us-east-1")

    flash("Session credentials cleared. Returned to Demo Mode.", "info")
    return redirect(url_for("auth.settings"))

@auth_bp.route("/test", methods=["POST"])
@login_required
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
