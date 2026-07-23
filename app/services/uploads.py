import os
import uuid
from flask import current_app


def allowed_file(filename):
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return ext in current_app.config["ALLOWED_IMAGE_EXTENSIONS"]


def _cloudinary_configured():
    return bool(current_app.config.get("CLOUDINARY_CLOUD_NAME"))


def save_upload(file_storage, subfolder=""):
    """Saves an uploaded image and returns a value image_url() can turn into
    a displayable URL.

    If Cloudinary env vars are set (CLOUDINARY_CLOUD_NAME / _API_KEY /
    _API_SECRET), the file is uploaded to Cloudinary and the full
    https:// secure_url is returned and stored directly — this is what
    should be used in production on Render's free tier, since the local
    disk is wiped on every redeploy/restart.

    Otherwise, falls back to saving on local disk under static/uploads
    (relative filename returned) — fine for local development.
    """
    if not file_storage or not file_storage.filename:
        return None
    if not allowed_file(file_storage.filename):
        return None

    unique_name = uuid.uuid4().hex

    if _cloudinary_configured():
        import cloudinary.uploader

        cloudinary.config(
            cloud_name=current_app.config["CLOUDINARY_CLOUD_NAME"],
            api_key=current_app.config["CLOUDINARY_API_KEY"],
            api_secret=current_app.config["CLOUDINARY_API_SECRET"],
            secure=True,
        )
        folder = f"oja/{subfolder}" if subfolder else "oja"
        result = cloudinary.uploader.upload(
            file_storage,
            public_id=unique_name,
            folder=folder,
            resource_type="image",
        )
        return result["secure_url"]

    ext = file_storage.filename.rsplit(".", 1)[-1].lower()
    filename = f"{unique_name}.{ext}"
    folder = os.path.join(current_app.config["UPLOAD_FOLDER"], subfolder)
    os.makedirs(folder, exist_ok=True)
    file_storage.save(os.path.join(folder, filename))

    return f"{subfolder}/{filename}" if subfolder else filename


def image_url(value, external=False):
    """Turns a stored image reference into a displayable URL. Handles both
    Cloudinary secure_urls (returned as-is) and local relative filenames
    (built into a /static/uploads/... URL). Safe to call with None."""
    if not value:
        return None
    if value.startswith("http://") or value.startswith("https://"):
        return value
    from flask import url_for

    return url_for("static", filename=f"uploads/{value}", _external=external)
