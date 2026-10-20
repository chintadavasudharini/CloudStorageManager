// CloudStorageManager Client JavaScript

let activePresignedBucket = "";
let activePresignedKey = "";
let activeDeleteBucket = "";
let activeDeleteKey = "";

// Table Search/Filter
document.addEventListener("DOMContentLoaded", function () {
    const filterInput = document.getElementById("fileFilterInput");
    if (filterInput) {
        filterInput.addEventListener("input", function (e) {
            const query = e.target.value.toLowerCase().trim();
            const rows = document.querySelectorAll(".object-item-row");
            rows.forEach((row) => {
                const name = row.getAttribute("data-name") || "";
                if (name.includes(query)) {
                    row.style.display = "";
                } else {
                    row.style.display = "none";
                }
            });
        });
    }

    // Drag and Drop Upload Setup
    const dropZone = document.getElementById("dropZone");
    const fileInput = document.getElementById("fileInput");
    const selectedFileInfo = document.getElementById("selectedFileInfo");
    const selectedFileName = document.getElementById("selectedFileName");
    const selectedFileSize = document.getElementById("selectedFileSize");
    const uploadForm = document.getElementById("uploadForm");

    if (dropZone && fileInput) {
        dropZone.addEventListener("click", () => fileInput.click());

        ["dragenter", "dragover"].forEach((eventName) => {
            dropZone.addEventListener(eventName, (e) => {
                e.preventDefault();
                dropZone.classList.add("dragover");
            });
        });

        ["dragleave", "drop"].forEach((eventName) => {
            dropZone.addEventListener(eventName, (e) => {
                e.preventDefault();
                dropZone.classList.remove("dragover");
            });
        });

        dropZone.addEventListener("drop", (e) => {
            if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
                fileInput.files = e.dataTransfer.files;
                handleFileSelected();
            }
        });

        fileInput.addEventListener("change", handleFileSelected);
    }

    function formatBytes(bytes) {
        if (bytes === 0) return "0 Bytes";
        const k = 1024;
        const sizes = ["Bytes", "KB", "MB", "GB"];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
    }

    function handleFileSelected() {
        if (fileInput && fileInput.files.length > 0) {
            const file = fileInput.files[0];
            selectedFileName.textContent = file.name;
            selectedFileSize.textContent = formatBytes(file.size);
            selectedFileInfo.classList.remove("d-none");
            selectedFileInfo.classList.add("d-flex");
        }
    }

    // AJAX Upload with Progress Bar
    if (uploadForm) {
        uploadForm.addEventListener("submit", function (e) {
            e.preventDefault();
            if (!fileInput.files || fileInput.files.length === 0) {
                alert("Please select a file to upload.");
                return;
            }

            const formData = new FormData(uploadForm);
            const progressBar = document.getElementById("uploadProgressBar");
            const progressContainer = document.getElementById("uploadProgressContainer");
            const submitBtn = document.getElementById("uploadSubmitBtn");
            const alertBox = document.getElementById("uploadAlert");

            progressContainer.classList.remove("d-none");
            progressBar.style.width = "0%";
            submitBtn.disabled = true;
            alertBox.classList.add("d-none");

            const xhr = new XMLHttpRequest();
            xhr.open("POST", "/api/upload", true);

            xhr.upload.onprogress = function (e) {
                if (e.lengthComputable) {
                    const percentComplete = Math.round((e.loaded / e.total) * 100);
                    progressBar.style.width = percentComplete + "%";
                }
            };

            xhr.onload = function () {
                submitBtn.disabled = false;
                if (xhr.status === 200) {
                    try {
                        const resp = JSON.parse(xhr.responseText);
                        if (resp.success) {
                            alertBox.className = "alert alert-success small";
                            alertBox.textContent = resp.message;
                            alertBox.classList.remove("d-none");
                            setTimeout(() => window.location.reload(), 900);
                        } else {
                            alertBox.className = "alert alert-danger small";
                            alertBox.textContent = resp.error || "Upload failed.";
                            alertBox.classList.remove("d-none");
                        }
                    } catch (err) {
                        alertBox.className = "alert alert-danger small";
                        alertBox.textContent = "Error parsing response: " + xhr.responseText;
                        alertBox.classList.remove("d-none");
                    }
                } else {
                    alertBox.className = "alert alert-danger small";
                    alertBox.textContent = "Upload failed with status " + xhr.status;
                    alertBox.classList.remove("d-none");
                }
            };

            xhr.onerror = function () {
                submitBtn.disabled = false;
                alertBox.className = "alert alert-danger small";
                alertBox.textContent = "Network error during upload.";
                alertBox.classList.remove("d-none");
            };

            xhr.send(formData);
        });
    }

    // Expiry Preset Radio Buttons Listener
    const presetRadios = document.querySelectorAll('input[name="expiryPreset"]');
    const expiryInput = document.getElementById("presignedExpiryInput");
    if (presetRadios && expiryInput) {
        presetRadios.forEach((radio) => {
            radio.addEventListener("change", function () {
                expiryInput.value = this.value;
            });
        });
    }

    // Presigned URL Generator Button
    const generatePresignedBtn = document.getElementById("generatePresignedBtn");
    if (generatePresignedBtn) {
        generatePresignedBtn.addEventListener("click", async function () {
            const expiration = parseInt(document.getElementById("presignedExpiryInput").value) || 3600;
            const resultArea = document.getElementById("presignedResultArea");
            const urlInput = document.getElementById("generatedUrlInput");
            const expiresAtSpan = document.getElementById("presignedExpiresAt");
            const openLink = document.getElementById("openUrlLink");

            generatePresignedBtn.disabled = true;
            generatePresignedBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Generating...';

            try {
                const res = await fetch("/api/presigned-url", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        bucket: activePresignedBucket,
                        key: activePresignedKey,
                        expiration: expiration,
                    }),
                });

                const data = await res.json();
                if (data.success) {
                    urlInput.value = data.url;
                    expiresAtSpan.textContent = data.expires_at;
                    openLink.href = data.url;
                    resultArea.classList.remove("d-none");
                } else {
                    alert("Error generating presigned URL: " + data.error);
                }
            } catch (err) {
                alert("Failed to contact server: " + err.message);
            } finally {
                generatePresignedBtn.disabled = false;
                generatePresignedBtn.innerHTML = '<i class="bi bi-lightning-charge-fill me-1"></i> Generate Presigned Link';
            }
        });
    }

    // Copy URL to Clipboard
    const copyUrlBtn = document.getElementById("copyUrlBtn");
    if (copyUrlBtn) {
        copyUrlBtn.addEventListener("click", function () {
            const urlInput = document.getElementById("generatedUrlInput");
            if (urlInput && urlInput.value) {
                navigator.clipboard.writeText(urlInput.value).then(() => {
                    copyUrlBtn.innerHTML = '<i class="bi bi-check2"></i> Copied!';
                    copyUrlBtn.classList.replace("btn-outline-primary", "btn-success");
                    setTimeout(() => {
                        copyUrlBtn.innerHTML = '<i class="bi bi-clipboard"></i> Copy';
                        copyUrlBtn.classList.replace("btn-success", "btn-outline-primary");
                    }, 2000);
                });
            }
        });
    }

    // Create Bucket Form
    const createBucketForm = document.getElementById("createBucketForm");
    if (createBucketForm) {
        createBucketForm.addEventListener("submit", async function (e) {
            e.preventDefault();
            const btn = document.getElementById("createBucketSubmitBtn");
            const alertBox = document.getElementById("createBucketAlert");
            const formData = new FormData(createBucketForm);

            btn.disabled = true;
            btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Creating...';
            alertBox.classList.add("d-none");

            try {
                const res = await fetch("/api/create-bucket", {
                    method: "POST",
                    body: formData,
                });
                const data = await res.json();
                if (data.success) {
                    alertBox.className = "alert alert-success small";
                    alertBox.textContent = data.message;
                    alertBox.classList.remove("d-none");
                    setTimeout(() => {
                        window.location.href = `/explorer?bucket=${encodeURIComponent(data.bucket_name)}`;
                    }, 800);
                } else {
                    alertBox.className = "alert alert-danger small";
                    alertBox.textContent = data.error || "Failed to create bucket.";
                    alertBox.classList.remove("d-none");
                }
            } catch (err) {
                alertBox.className = "alert alert-danger small";
                alertBox.textContent = "Network error: " + err.message;
                alertBox.classList.remove("d-none");
            } finally {
                btn.disabled = false;
                btn.innerHTML = "Create Bucket";
            }
        });
    }

    // Create Folder Form
    const createFolderForm = document.getElementById("createFolderForm");
    if (createFolderForm) {
        createFolderForm.addEventListener("submit", async function (e) {
            e.preventDefault();
            const btn = document.getElementById("createFolderSubmitBtn");
            const alertBox = document.getElementById("createFolderAlert");
            const formData = new FormData(createFolderForm);

            btn.disabled = true;
            btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Creating...';
            alertBox.classList.add("d-none");

            try {
                const res = await fetch("/api/create-folder", {
                    method: "POST",
                    body: formData,
                });
                const data = await res.json();
                if (data.success) {
                    alertBox.className = "alert alert-success small";
                    alertBox.textContent = data.message;
                    alertBox.classList.remove("d-none");
                    setTimeout(() => window.location.reload(), 800);
                } else {
                    alertBox.className = "alert alert-danger small";
                    alertBox.textContent = data.error || "Failed to create folder.";
                    alertBox.classList.remove("d-none");
                }
            } catch (err) {
                alertBox.className = "alert alert-danger small";
                alertBox.textContent = "Network error: " + err.message;
                alertBox.classList.remove("d-none");
            } finally {
                btn.disabled = false;
                btn.innerHTML = "Create Folder";
            }
        });
    }

    // Confirm Delete Action
    const confirmDeleteBtn = document.getElementById("confirmDeleteBtn");
    if (confirmDeleteBtn) {
        confirmDeleteBtn.addEventListener("click", async function () {
            confirmDeleteBtn.disabled = true;
            confirmDeleteBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Deleting...';

            try {
                const res = await fetch("/api/delete", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        bucket: activeDeleteBucket,
                        key: activeDeleteKey,
                    }),
                });
                const data = await res.json();
                if (data.success) {
                    window.location.reload();
                } else {
                    alert("Delete failed: " + data.error);
                }
            } catch (err) {
                alert("Network error: " + err.message);
            } finally {
                confirmDeleteBtn.disabled = false;
                confirmDeleteBtn.innerHTML = '<i class="bi bi-trash-fill me-1"></i> Delete Permanently';
            }
        });
    }
});

// Helper: Open Presigned Modal
function openPresignedModal(bucket, key, fileName) {
    activePresignedBucket = bucket;
    activePresignedKey = key;
    document.getElementById("presignedObjectKey").value = `${bucket}/${key}`;
    document.getElementById("presignedResultArea").classList.add("d-none");
    document.getElementById("generatedUrlInput").value = "";

    const modal = new bootstrap.Modal(document.getElementById("presignedModal"));
    modal.show();
}

// Helper: Open Metadata Modal
async function openMetadataModal(bucket, key) {
    const loading = document.getElementById("metadataLoading");
    const content = document.getElementById("metadataContent");

    loading.classList.remove("d-none");
    content.classList.add("d-none");

    const modal = new bootstrap.Modal(document.getElementById("metadataModal"));
    modal.show();

    try {
        const res = await fetch(`/api/metadata?bucket=${encodeURIComponent(bucket)}&key=${encodeURIComponent(key)}`);
        const resp = await res.json();

        if (resp.success) {
            const d = resp.data;
            document.getElementById("metaKey").textContent = d.key;
            document.getElementById("metaBucket").textContent = d.bucket;
            document.getElementById("metaContentType").textContent = d.content_type;
            document.getElementById("metaSize").textContent = d.content_length + " bytes";
            document.getElementById("metaLastModified").textContent = d.last_modified;
            document.getElementById("metaETag").textContent = d.etag;
            document.getElementById("metaStorageClass").textContent = d.storage_class;
            document.getElementById("metaEncryption").textContent = d.server_side_encryption;

            loading.classList.add("d-none");
            content.classList.remove("d-none");
        } else {
            alert("Failed to load metadata: " + resp.error);
        }
    } catch (err) {
        alert("Error fetching metadata: " + err.message);
    }
}

// Helper: Confirm Delete Modal
function confirmDelete(bucket, key, fileName) {
    activeDeleteBucket = bucket;
    activeDeleteKey = key;
    document.getElementById("deleteTargetKey").textContent = `${bucket} / ${key}`;
    const modal = new bootstrap.Modal(document.getElementById("deleteModal"));
    modal.show();
}
