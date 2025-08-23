"""Learning endpoints."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query

from application.use_cases.learning import (
    StartLearningSessionUseCase,
    GetNextQuestionUseCase,
    SubmitAnswerUseCase,
    EndSessionUseCase,
    ReviewCardUseCase,
    RequestHintUseCase
)
from application.dto.request import (
    StartSessionRequest,
    GetNextQuestionRequest,
    SubmitAnswerRequest,
    ReviewCardRequest,
    RequestHintRequest
)
from application.dto.response import (
    SessionResponse,
    QuestionResponse,
    AnswerFeedbackResponse,
    HintResponse
)
from ..dependencies import get_current_user_id, get_use_case

router = APIRouter()


@router.post("/sessions/start", response_model=SessionResponse)
async def start_session(
    request: StartSessionRequest,
    user_id: UUID = Depends(get_current_user_id),
    use_case: StartLearningSessionUseCase = Depends(get_use_case("start_session_use_case"))
):
    """Start a new learning session."""
    return await use_case.execute(request, user_id)


@router.get("/sessions/current", response_model=Optional[SessionResponse])
async def get_current_session(
    user_id: UUID = Depends(get_current_user_id),
    use_case = Depends(get_use_case("get_current_session_use_case"))
):
    """Get current active session."""
    return await use_case.execute(user_id)


@router.post("/sessions/{session_id}/end")
async def end_session(
    session_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    use_case: EndSessionUseCase = Depends(get_use_case("end_session_use_case"))
):
    """End a learning session."""
    await use_case.execute(session_id, user_id)
    return {"message": "Session ended successfully"}


@router.get("/questions/next", response_model=Optional[QuestionResponse])
async def get_next_question(
    session_id: UUID = Query(..., description="Session ID"),
    facet_id: Optional[UUID] = Query(None, description="Facet ID for filtering"),
    user_id: UUID = Depends(get_current_user_id),
    use_case: GetNextQuestionUseCase = Depends(get_use_case("get_next_question_use_case"))
):
    """Get next question for the session."""
    request = GetNextQuestionRequest(
        user_id=user_id,
        session_id=session_id,
        facet_id=facet_id
    )
    return await use_case.execute(request)


@router.post("/questions/{question_id}/answer", response_model=AnswerFeedbackResponse)
async def submit_answer(
    question_id: UUID,
    request: SubmitAnswerRequest,
    user_id: UUID = Depends(get_current_user_id),
    use_case: SubmitAnswerUseCase = Depends(get_use_case("submit_answer_use_case"))
):
    """Submit answer for a question."""
    request.question_id = question_id
    return await use_case.execute(request, user_id)


@router.post("/questions/{question_id}/hint", response_model=HintResponse)
async def request_hint(
    question_id: UUID,
    session_id: UUID = Query(...),
    hint_level: int = Query(1, ge=1, le=3),
    user_id: UUID = Depends(get_current_user_id),
    use_case: RequestHintUseCase = Depends(get_use_case("request_hint_use_case"))
):
    """Request a hint for a question."""
    request = RequestHintRequest(
        question_id=question_id,
        session_id=session_id,
        hint_level=hint_level
    )
    return await use_case.execute(request, user_id)


@router.post("/cards/{card_id}/review")
async def review_card(
    card_id: UUID,
    request: ReviewCardRequest,
    user_id: UUID = Depends(get_current_user_id),
    use_case: ReviewCardUseCase = Depends(get_use_case("review_card_use_case"))
):
    """Review a spaced repetition card."""
    request.card_id = card_id
    return await use_case.execute(request, user_id)


@router.get("/cards/due")
async def get_due_cards(
    facet_id: Optional[UUID] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    user_id: UUID = Depends(get_current_user_id),
    use_case = Depends(get_use_case("get_due_cards_use_case"))
):
    """Get cards due for review."""
    return await use_case.execute(user_id, facet_id, limit)


@router.get("/cards/forecast")
async def get_review_forecast(
    facet_id: Optional[UUID] = Query(None),
    days: int = Query(30, ge=1, le=365),
    user_id: UUID = Depends(get_current_user_id),
    use_case = Depends(get_use_case("get_review_forecast_use_case"))
):
    """Get forecast of upcoming reviews."""
    return await use_case.execute(user_id, facet_id, days)