"""Content management endpoints."""

from typing import Optional, List
from uuid import UUID
from pathlib import Path

from fastapi import APIRouter, Depends, Query, UploadFile, File, BackgroundTasks, HTTPException, status

from application.use_cases.content import (
    ImportQuestionsUseCase,
    GetContentTreeUseCase,
    SearchContentUseCase
)
from application.dto.request import (
    ImportQuestionsRequest,
    GetContentTreeRequest,
    SearchContentRequest
)
from application.dto.response import (
    ContentNodeResponse,
    ContentTreeResponse,
    ImportResultResponse
)
from ..dependencies import get_current_user_id, get_optional_user, get_use_case

router = APIRouter()


@router.get("/tree", response_model=ContentTreeResponse)
async def get_content_tree(
        root_level: str = Query("topic"),
        root_id: Optional[UUID] = Query(None),
        max_depth: int = Query(4, ge=1, le=4),
        include_progress: bool = Query(False),
        user_id: Optional[UUID] = Depends(get_optional_user),
        use_case: GetContentTreeUseCase = Depends(get_use_case("get_content_tree_use_case"))
):
    """Get hierarchical content tree."""
    request = GetContentTreeRequest(
        root_level=root_level,
        root_id=root_id,
        max_depth=max_depth,
        include_stats=True,
        include_progress=include_progress,
        user_id=user_id if include_progress else None
    )

    return await use_case.execute(request)


@router.get("/topics", response_model=List[ContentNodeResponse])
async def list_topics(
        active_only: bool = Query(True),
        use_case=Depends(get_use_case("list_topics_use_case"))
):
    """List all topics."""
    return await use_case.execute(active_only)


@router.get("/topics/{topic_id}/subtopics", response_model=List[ContentNodeResponse])
async def list_subtopics(
        topic_id: UUID,
        active_only: bool = Query(True),
        use_case=Depends(get_use_case("list_subtopics_use_case"))
):
    """List subtopics for a topic."""
    return await use_case.execute(topic_id, active_only)


@router.get("/subtopics/{subtopic_id}/leaves", response_model=List[ContentNodeResponse])
async def list_leaves(
        subtopic_id: UUID,
        active_only: bool = Query(True),
        use_case=Depends(get_use_case("list_leaves_use_case"))
):
    """List leaves for a subtopic."""
    return await use_case.execute(subtopic_id, active_only)


@router.get("/leaves/{leaf_id}/facets", response_model=List[ContentNodeResponse])
async def list_facets(
        leaf_id: UUID,
        active_only: bool = Query(True),
        use_case=Depends(get_use_case("list_facets_use_case"))
):
    """List facets for a leaf."""
    return await use_case.execute(leaf_id, active_only)


@router.get("/facets/{facet_id}", response_model=ContentNodeResponse)
async def get_facet(
        facet_id: UUID,
        use_case=Depends(get_use_case("get_facet_use_case"))
):
    """Get facet details."""
    return await use_case.execute(facet_id)


@router.get("/search", response_model=List[ContentNodeResponse])
async def search_content(
        query: str = Query(..., min_length=2),
        level: Optional[str] = Query(None),
        limit: int = Query(20, ge=1, le=100),
        use_case: SearchContentUseCase = Depends(get_use_case("search_content_use_case"))
):
    """Search content nodes."""
    request = SearchContentRequest(
        query=query,
        level=level,
        limit=limit
    )

    return await use_case.execute(request)


@router.post("/import", response_model=ImportResultResponse)
async def import_questions(
        file: UploadFile = File(...),
        dry_run: bool = Query(False),
        background_tasks: BackgroundTasks = None,
        user_id: UUID = Depends(get_current_user_id),
        use_case: ImportQuestionsUseCase = Depends(get_use_case("import_questions_use_case"))
):
    """Import questions from JSON file."""
    # Validate file type
    if not file.filename.endswith('.json'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only JSON files are supported"
        )

    # Save uploaded file temporarily
    import tempfile
    with tempfile.NamedTemporaryFile(delete=False, suffix='.json') as tmp_file:
        content = await file.read()
        tmp_file.write(content)
        tmp_path = tmp_file.name

    request = ImportQuestionsRequest(
        file_path=tmp_path,
        source="admin_imported",
        dry_run=dry_run
    )

    # Execute import
    result = await use_case.execute(request)

    # Clean up temp file
    Path(tmp_path).unlink()

    return result


@router.post("/import/bulk")
async def bulk_import(
        files: List[UploadFile] = File(...),
        background_tasks: BackgroundTasks = None,
        user_id: UUID = Depends(get_current_user_id),
        use_case=Depends(get_use_case("bulk_import_use_case"))
):
    """Bulk import multiple question files."""
    # Validate files
    for file in files:
        if not file.filename.endswith('.json'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file type: {file.filename}"
            )

    # Save files and queue for processing
    file_paths = []
    import tempfile

    for file in files:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.json') as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            file_paths.append(tmp_file.name)

    # Queue background task
    if background_tasks:
        background_tasks.add_task(
            use_case.execute,
            file_paths,
            user_id
        )

    return {
        "message": f"Queued {len(files)} files for import",
        "files": [f.filename for f in files]
    }