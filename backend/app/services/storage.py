import io
import logging
import uuid
import zipfile
from datetime import datetime, timezone

from fastapi import HTTPException, UploadFile

from app.config import settings
from app.models.db import get_authenticated_client

logger = logging.getLogger(__name__)

BUCKET_NAME = "syllabi"
MAX_FILE_SIZE = settings.max_file_size_mb * 1024 * 1024


def _safe_filename(filename: str | None) -> str:
    if not filename:
        return "upload"
    return filename.rsplit("/", 1)[-1].rsplit("\\", 1)[-1].replace(" ", "_")


async def validate_total_upload_size(files: list[UploadFile]) -> None:
    total_size = 0
    for file in files:
        await file.seek(0)
        total_size += len(await file.read())
        await file.seek(0)

    if total_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File size exceeds {settings.max_file_size_mb}MB limit",
        )


async def upload_file(file: UploadFile, user_id: str, access_token: str) -> dict[str, str | int]:
    await file.seek(0)
    content = await file.read()
    file_size = len(content)

    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File size exceeds {settings.max_file_size_mb}MB limit",
        )

    storage_path = (
        f"{user_id}/"
        f"{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_"
        f"{str(uuid.uuid4())[:8]}_"
        f"{_safe_filename(file.filename)}"
    )

    try:
        get_authenticated_client(access_token).storage.from_(BUCKET_NAME).upload(
            path=storage_path,
            file=content,
            file_options={
                "content-type": file.content_type or "application/octet-stream"
            },
        )
    except Exception as exc:
        logger.exception("Failed to upload file to storage")
        raise HTTPException(status_code=500, detail="Failed to upload file") from exc

    return {"path": storage_path, "size": file_size}


async def upload_files(
    files: list[UploadFile],
    user_id: str,
    access_token: str,
) -> dict[str, list[str] | int]:
    uploaded_paths: list[str] = []
    total_size = 0

    try:
        for file in files:
            result = await upload_file(file, user_id, access_token)
            uploaded_paths.append(str(result["path"]))
            total_size += int(result["size"])
    except Exception:
        for path in uploaded_paths:
            await delete_file_best_effort(path, access_token)
        raise

    return {"paths": uploaded_paths, "total_size": total_size}


async def download_file(storage_path: str, access_token: str) -> bytes:
    try:
        return get_authenticated_client(access_token).storage.from_(BUCKET_NAME).download(
            storage_path
        )
    except Exception as exc:
        logger.exception("Failed to download file: %s", storage_path)
        raise HTTPException(status_code=404, detail="File not found") from exc


async def delete_file(storage_path: str, access_token: str) -> None:
    try:
        get_authenticated_client(access_token).storage.from_(BUCKET_NAME).remove(
            [storage_path]
        )
    except Exception as exc:
        logger.exception("Failed to delete file: %s", storage_path)
        raise HTTPException(
            status_code=503,
            detail=f"Failed to delete file from storage: {storage_path}",
        ) from exc


async def delete_file_best_effort(storage_path: str, access_token: str) -> bool:
    try:
        get_authenticated_client(access_token).storage.from_(BUCKET_NAME).remove(
            [storage_path]
        )
    except Exception:
        logger.warning("Best-effort delete failed: %s", storage_path)
        return False

    return True


async def download_files_as_zip(storage_paths: list[str], access_token: str) -> bytes:
    zip_buffer = io.BytesIO()
    client = get_authenticated_client(access_token)

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for index, path in enumerate(storage_paths):
            try:
                content = client.storage.from_(BUCKET_NAME).download(path)
            except Exception as exc:
                logger.exception("Failed to download file for zip: %s", path)
                raise HTTPException(
                    status_code=503,
                    detail=f"Failed to download file: {path}. Please try again.",
                ) from exc

            filename = path.split("/")[-1] if "/" in path else f"file_{index}"
            zip_file.writestr(filename, content)

    zip_buffer.seek(0)
    return zip_buffer.read()
