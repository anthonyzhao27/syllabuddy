import logging
from collections import Counter

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.middleware.auth import AuthenticatedUser, get_current_user
from app.models.schemas import ParseResponse
from app.services.extraction import _is_image, extract_text, extract_text_from_images
from app.services.llm import extract_events
from app.services import storage as storage_service
from app.services import syllabi as syllabi_service

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/", response_model=ParseResponse)
async def parse_syllabus(
    files: list[UploadFile] = File(default=[]),
    syllabus_name: str | None = Form(default=None),
    user: AuthenticatedUser = Depends(get_current_user),
) -> ParseResponse:
    """Extract assignments and due dates from uploaded files."""
    if not files or not files[0].filename:
        raise HTTPException(status_code=400, detail="Please upload a file.")

    await storage_service.validate_total_upload_size(files)

    if _is_image(files[0]):
        if not all(_is_image(file) for file in files):
            raise HTTPException(
                status_code=400,
                detail="When uploading screenshots, all files must be images.",
            )
        text = await extract_text_from_images(files)
        source_type = "screenshots"
        original_filename = None
    else:
        if len(files) > 1:
            raise HTTPException(
                status_code=400,
                detail="Only one document file allowed. For multiple images, use screenshots.",
            )
        text = await extract_text(files[0])
        source_type = "file"
        original_filename = files[0].filename

    try:
        events = await extract_events(text)
    except ValueError as e:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to parse LLM response: {e}",
        )
    except HTTPException:
        raise
    except Exception:
        logger.exception("LLM request failed during syllabus parsing")
        raise HTTPException(
            status_code=502,
            detail="LLM service unavailable. Please try again.",
        )

    course_codes = [event.course.strip() for event in events if event.course.strip()]
    course_code = Counter(course_codes).most_common(1)[0][0] if course_codes else None

    storage_paths: list[str] = []
    syllabus: dict[str, object] | None = None

    try:
        upload_result = await storage_service.upload_files(
            files,
            user.id,
            user.access_token,
        )
        storage_paths_value = upload_result["paths"]
        if not isinstance(storage_paths_value, list):
            raise RuntimeError("Invalid upload response")
        storage_paths = [path for path in storage_paths_value if isinstance(path, str)]
        total_size = upload_result["total_size"]
        if not isinstance(total_size, int):
            raise RuntimeError("Invalid upload response")

        syllabus = await syllabi_service.create_syllabus(
            user.access_token,
            user.id,
            name=syllabus_name or original_filename or f"Syllabus - {course_code or 'Unknown'}",
            source_type=source_type,
            course_code=course_code,
            original_filename=original_filename,
            storage_paths=storage_paths,
            total_file_size_bytes=total_size,
        )
        syllabus_id = syllabus.get("id")
        if not isinstance(syllabus_id, str):
            raise RuntimeError("Invalid syllabus response")

        await syllabi_service.save_events(
            user.access_token,
            syllabus_id,
            user.id,
            events,
        )
    except HTTPException:
        raise
    except Exception:
        for path in storage_paths:
            await storage_service.delete_file_best_effort(path, user.access_token)
        if syllabus is not None:
            syllabus_id = syllabus.get("id")
            if isinstance(syllabus_id, str):
                try:
                    await syllabi_service.delete_syllabus(user.access_token, syllabus_id)
                except Exception:
                    pass
        raise HTTPException(
            status_code=503,
            detail="Failed to save parsed syllabus. Please try again.",
        )

    return ParseResponse(syllabus_id=syllabus_id, events=events)
