# CloudStorageManager ☁️

A web-based interface for managing AWS S3 buckets — upload, download, organize, and share files securely with presigned URLs and IAM-based access controls.

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.x-black.svg)](https://flask.palletsprojects.com/)
[![AWS SDK](https://img.shields.io/badge/Boto3-AWS%20SDK-orange.svg)](https://aws.amazon.com/sdk-for-python/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![GitHub Repository](https://img.shields.io/badge/GitHub-CloudStorageManager-blue?logo=github)](https://github.com/chintadavasudharini/CloudStorageManager)

---

## 🌟 Overview

**CloudStorageManager** provides an intuitive, responsive cloud storage console for AWS S3. It eliminates the need for non-technical users to access the complex AWS Management Console while enforcing the principle of least privilege, strict bucket privacy, and cryptographic temporary file sharing using **S3 Presigned URLs**.

---

## 🛠️ Technical Stack

- **Backend:** Python 3, Flask, Boto3 (AWS SDK for Python)
- **Cloud Infrastructure:** AWS S3 (Simple Storage Service), AWS IAM (Identity and Access Management)
- **Security:** Presigned Temporary URLs, SSL/TLS Data Transfer, Encrypted Sessions
- **Testing & Emulation:** Moto (AWS Local Mocking Engine), Pytest

---

## 🚀 Key Features & Implementations

### 1. Direct AWS S3 Integration
- **Verified Credentials:** Authenticates against AWS using IAM Access Keys via `boto3`.
- **Bucket Management:** List existing S3 buckets and provision new buckets with custom regional configurations (`LocationConstraint`).
- **Hierarchical Navigation:** Drill down into folders and nested paths using virtual S3 prefixes and delimiters (`/`).
- **Object Metadata Retrieval:** Inspect object file size, content MIME type, last modified timestamp, ETag hash, storage class (`STANDARD`, `GLACIER`, etc.), and server-side encryption.

### 2. Secure Sharing with Presigned URLs
- **Private by Default:** Target S3 buckets remain completely private with zero public read/write permissions.
- **Configurable Expirations:** Generate cryptographically signed URLs valid for a customizable timeframe (e.g., 15 minutes, 1 hour, 6 hours, 24 hours, or custom seconds up to 7 days).
- **Time-Limited Access:** Third parties can stream or download designated files securely without needing AWS IAM credentials or public bucket ACLs.

### 3. File Operations & Organization
- **Drag-and-Drop Uploads:** Upload files seamlessly with AJAX progress bars and automatic MIME detection.
- **Direct Downloads:** Stream and download files straight from S3.
- **Virtual Directory Support:** Create directories and maintain organized folder hierarchies.
- **Object Deletion:** Safe deletion workflows with confirmation dialogs.
- **Instant Search/Filter:** Filter objects and folders in real time.

### 4. User Authentication & Profile Security
- **Secure Signup & Signin:** Encrypted password hashing with `Werkzeug` PBKDF2/SHA256.
- **SQLite Database:** Zero-config persistent user account management.
- **Session Protection:** `@login_required` route guards preventing unauthorized console access.
- **One-Click Demo Account:** Pre-seeded account (`demo@cloudstorage.com` / `demo1234`) with instant autofill for zero-barrier evaluation.

### 5. Zero-Friction Demo Mode
- Built-in **Mock AWS S3** powered by `moto`.
- Test all uploads, folder structures, metadata lookups, and presigned URL sharing immediately without configuring real AWS credentials or incurring AWS costs.

---

## 🔒 Security & IAM Architecture

### Recommended AWS IAM Policy (Least Privilege)
To connect CloudStorageManager to your AWS account, create an IAM User or Role with the following minimal policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowBucketListing",
      "Effect": "Allow",
      "Action": [
        "s3:ListAllMyBuckets",
        "s3:GetBucketLocation"
      ],
      "Resource": "*"
    },
    {
      "Sid": "AllowObjectOperations",
      "Effect": "Allow",
      "Action": [
        "s3:ListBucket",
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject"
      ],
      "Resource": [
        "arn:aws:s3:::*",
        "arn:aws:s3:::*/*"
      ]
    }
  ]
}
```

---

## 📁 Project Structure

```text
cloudstoragemanager/
├── app/
│   ├── __init__.py           # Flask application factory & context injection
│   ├── config.py             # App configuration & environment loader
│   ├── s3_service.py         # S3 service layer (Boto3 integration & Moto demo)
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── main.py           # Explorer dashboard, download, & inline views
│   │   ├── api.py            # REST endpoints (upload, delete, presigned URL)
│   │   └── auth.py           # IAM credentials & session management
│   ├── static/
│   │   ├── css/style.css     # UI styles & animations
│   │   └── js/app.js         # Client-side file upload, filter, & modal handlers
│   └── templates/
│       ├── base.html         # Base template with responsive navigation & footer
│       ├── explorer.html     # S3 bucket and object manager dashboard
│       └── settings.html     # AWS IAM credential configuration & policy guide
├── tests/
│   ├── test_s3_service.py    # Unit tests for S3 service operations
│   └── test_routes.py        # Integration tests for Flask endpoints
├── .env.example              # Example environment configuration
├── requirements.txt          # Python dependencies
├── run.py                    # Application entry point
└── README.md                 # Project documentation
```

---

## ⚡ Quickstart Guide

### 1. Clone the Repository
```bash
git clone https://github.com/chintadavasudharini/CloudStorageManager.git
cd CloudStorageManager
```

### 2. Set Up Virtual Environment (Recommended)
```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables (Optional)
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

You can configure:
```ini
FLASK_SECRET_KEY=your-secret-key
AWS_ACCESS_KEY_ID=your-aws-access-key-id
AWS_SECRET_ACCESS_KEY=your-aws-secret-access-key
AWS_DEFAULT_REGION=us-east-1
ENABLE_DEMO_MODE=true
```
*(Note: If no AWS keys are specified, CloudStorageManager automatically runs in Demo Mode with mock data).*

### 5. Launch the Application
```bash
python run.py
```
Open your browser and navigate to: **[http://localhost:5000](http://localhost:5000)**

---

## 🧪 Running Automated Tests

Run the test suite using `pytest`:
```bash
python -m pytest tests -v
```

All 16 test cases covering bucket creation, uploads, downloads, presigned URL generation, metadata retrieval, and route endpoints will run against the isolated mock environment.

---

## 🤝 Contributing

Contributions, bug reports, and feature requests are welcome!
1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.
