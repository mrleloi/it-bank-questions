"""Question management endpoints."""

from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from application.dto.request import CreateQuestionRequest
from application.dto.response import QuestionResponse
from application.dto.common import PaginationResponse
from ..dependencies import (
    get_current_user_id,
    get_pagination,
    get_use_case,
    get_question_repository
)

router = APIRouter()


@router.get("/{question_id}", response_model=QuestionResponse)
async def get_question(
        question_id: UUID,
        user_id: Optional[UUID] = Depends(get_current_user_id),
        repo=Depends(get_question_repository)
):
    """Get question by ID."""
    question = await repo.get_by_id(question_id)
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found"
        )

    # Get card info if user is authenticated
    card = None
    if user_id:
        from ..dependencies import get_container
        container = get_container()
        sr_repo = container.spaced_repetition_repository()
        card = await sr_repo.get_by_user_and_question(user_id, question_id)

    from application.mappers import QuestionMapper
    return QuestionMapper.to_response_dto(question, card)


@router.get("/", response_model=PaginationResponse[QuestionResponse])
async def list_questions(
        facet_id: Optional[UUID] = Query(None),
        question_type: Optional[str] = Query(None),
        difficulty: Optional[int] = Query(None, ge=1, le=5),
        pagination=Depends(get_pagination),
        repo=Depends(get_question_repository)
):
    """List questions with filters."""
    from domain.value_objects import QuestionType, DifficultyLevel

    q_type = QuestionType(question_type) if question_type else None
    d_level = DifficultyLevel(difficulty) if difficulty else None

    questions = await repo.get_by_facet(
        facet_id=facet_id,
        question_type=q_type,
        difficulty=d_level,
        limit=pagination.limit,
        offset=pagination.offset
    )

    total = await repo.count(facet_id=facet_id)

    from application.mappers import QuestionMapper
    items = [QuestionMapper.to_response_dto(q) for q in questions]

    return PaginationResponse.create(
        items=items,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size
    )


@router.post("/", response_model=QuestionResponse, status_code=status.HTTP_201_CREATED)
async def create_question(
        request: CreateQuestionRequest,
        user_id: UUID = Depends(get_current_user_id),
        use_case=Depends(get_use_case("create_question_use_case"))
):
    """Create a new question."""
    return await use_case.execute(request, user_id)


@router.get("/search", response_model=List[QuestionResponse])
async def search_questions(
        query: str = Query(..., min_length=2),
        facet_id: Optional[UUID] = Query(None),
        limit: int = Query(20, ge=1, le=100),
        repo=Depends(get_question_repository)
):
    """Search questions by text."""
    questions = await repo.search_questions(
        query=query,
        facet_id=facet_id,
        limit=limit
    )

    from application.mappers import QuestionMapper
    return [QuestionMapper.to_response_dto(q) for q in questions]


@router.get("/random", response_model=List[QuestionResponse])
async def get_random_questions(
        facet_id: UUID = Query(...),
        count: int = Query(10, ge=1, le=50),
        question_type: Optional[str] = Query(None),
        repo=Depends(get_question_repository)
):
    """Get random questions from a facet."""
    from domain.value_objects import QuestionType

    q_type = QuestionType(question_type) if question_type else None

    questions = await repo.get_random_questions(
        facet_id=facet_id,
        count=count,
        question_type=q_type
    )

    from application.mappers import QuestionMapper
    return [QuestionMapper.to_response_dto(q) for q in questions]