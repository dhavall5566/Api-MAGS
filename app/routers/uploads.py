from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.services.imagekit import ImageKitError, get_upload_auth_params, upload_image_bytes

router = APIRouter(prefix="/api/uploads", tags=["uploads"])


@router.get("/auth")
def imagekit_auth():
    try:
        return get_upload_auth_params()
    except ImageKitError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/image")
async def upload_image(
    file: UploadFile = File(...),
    folder: str | None = Form(None),
):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image files are allowed")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file")

    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File must be 10 MB or smaller")

    try:
        result = await upload_image_bytes(
            filename=file.filename or "upload.jpg",
            content=content,
            content_type=file.content_type,
            folder=folder,
        )
    except ImageKitError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    if not result.get("url"):
        raise HTTPException(status_code=502, detail="ImageKit did not return a URL")

    return result
