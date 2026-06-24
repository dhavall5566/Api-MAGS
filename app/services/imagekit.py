from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
import time
from typing import Any

import httpx

from app.config import settings

IMAGEKIT_UPLOAD_URL = "https://upload.imagekit.io/api/v1/files/upload"


class ImageKitError(Exception):
    pass


def _basic_auth_header() -> str:
    token = base64.b64encode(f"{settings.imagekit_private_key}:".encode()).decode()
    return f"Basic {token}"


def get_upload_auth_params() -> dict[str, str | int]:
    if not settings.imagekit_configured:
        raise ImageKitError("ImageKit is not configured")

    token = secrets.token_hex(16)
    expire = int(time.time()) + 3600
    signature = hmac.new(
        settings.imagekit_private_key.encode(),
        f"{token}{expire}".encode(),
        hashlib.sha1,
    ).hexdigest()

    return {
        "token": token,
        "expire": expire,
        "signature": signature,
        "publicKey": settings.imagekit_public_key,
        "urlEndpoint": settings.imagekit_url_endpoint,
    }


async def upload_image_bytes(
    *,
    filename: str,
    content: bytes,
    content_type: str | None,
    folder: str | None = None,
) -> dict[str, Any]:
    if not settings.imagekit_configured:
        raise ImageKitError("ImageKit private key is missing. Set IMAGEKIT_PRIVATE_KEY in .env")

    upload_folder = folder or settings.imagekit_upload_folder
    headers = {"Authorization": _basic_auth_header()}
    files = {"file": (filename, content, content_type or "application/octet-stream")}
    data = {
        "fileName": filename,
        "folder": upload_folder,
        "useUniqueFileName": "true",
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            IMAGEKIT_UPLOAD_URL,
            headers=headers,
            files=files,
            data=data,
        )

    if response.status_code >= 400:
        detail = response.text
        try:
            payload = response.json()
            detail = payload.get("message") or payload.get("error") or detail
        except Exception:
            pass
        raise ImageKitError(f"ImageKit upload failed: {detail}")

    payload = response.json()
    return {
        "url": payload.get("url"),
        "fileId": payload.get("fileId"),
        "filePath": payload.get("filePath"),
        "thumbnailUrl": payload.get("thumbnailUrl"),
        "name": payload.get("name"),
        "fileType": payload.get("fileType"),
    }
