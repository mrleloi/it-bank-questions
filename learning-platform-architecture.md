# Learning Platform Architecture Design

## 🏗️ High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend (Next.js)                    │
├─────────────────────────────────────────────────────────────┤
│                    API Gateway (FastAPI)                     │
├─────────────────────────────────────────────────────────────┤
│                  Application Layer (Django)                  │
│  ┌─────────────┬─────────────┬─────────────┬────────────┐  │
│  │   Auth      │  Learning   │  Content    │  Analytics │  │
│  │  Service    │   Service   │   Service   │   Service  │  │
│  └─────────────┴─────────────┴─────────────┴────────────┘  │
├─────────────────────────────────────────────────────────────┤
│                      Domain Layer                            │
│  ┌─────────────┬─────────────┬─────────────┬────────────┐  │
│  │   User      │  Question   │  Learning   │  Progress  │  │
│  │  Entities   │  Entities   │  Entities   │  Entities  │  │
│  └─────────────┴─────────────┴─────────────┴────────────┘  │
├─────────────────────────────────────────────────────────────┤
│                  Infrastructure Layer                        │
│  ┌──────────┬──────────┬──────────┬──────────┬─────────┐  │
│  │ MariaDB  │  Redis   │  Celery  │   S3     │   AI    │  │
│  │          │  Cache   │  Queue   │ Storage  │ Service │  │
│  └──────────┴──────────┴──────────┴──────────┴─────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## 📁 Project Structure

### Backend (Django + FastAPI)

```
learning-platform-backend/
├── src/
│   ├── core/                      # Core configurations
│   │   ├── __init__.py
│   │   ├── settings/
│   │   │   ├── base.py
│   │   │   ├── development.py
│   │   │   ├── production.py
│   │   │   └── testing.py
│   │   ├── asgi.py
│   │   ├── wsgi.py
│   │   └── urls.py
│   │
│   ├── domain/                    # Domain Layer (Business Logic)
│   │   ├── __init__.py
│   │   ├── entities/
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── question.py
│   │   │   ├── learning_session.py
│   │   │   ├── progress.py
│   │   │   └── content_hierarchy.py
│   │   ├── value_objects/
│   │   │   ├── __init__.py
│   │   │   ├── difficulty_level.py
│   │   │   ├── question_type.py
│   │   │   └── learning_metrics.py
│   │   ├── repositories/          # Repository Interfaces
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── user_repository.py
│   │   │   ├── question_repository.py
│   │   │   └── progress_repository.py
│   │   ├── services/              # Domain Services
│   │   │   ├── __init__.py
│   │   │   ├── spaced_repetition_service.py
│   │   │   ├── learning_path_service.py
│   │   │   └── content_hierarchy_service.py
│   │   └── events/                # Domain Events
│   │       ├── __init__.py
│   │       ├── base.py
│   │       ├── question_events.py
│   │       └── learning_events.py
│   │
│   ├── application/               # Application Layer (Use Cases)
│   │   ├── __init__.py
│   │   ├── use_cases/
│   │   │   ├── __init__.py
│   │   │   ├── auth/
│   │   │   │   ├── register_user.py
│   │   │   │   └── authenticate_user.py
│   │   │   ├── learning/
│   │   │   │   ├── start_learning_session.py
│   │   │   │   ├── submit_answer.py
│   │   │   │   ├── get_next_question.py
│   │   │   │   └── update_progress.py
│   │   │   └── content/
│   │   │       ├── import_questions.py
│   │   │       ├── get_content_hierarchy.py
│   │   │       └── manage_resources.py
│   │   ├── dto/                   # Data Transfer Objects
│   │   │   ├── __init__.py
│   │   │   ├── request/
│   │   │   │   ├── auth_dto.py
│   │   │   │   ├── learning_dto.py
│   │   │   │   └── content_dto.py
│   │   │   └── response/
│   │   │       ├── user_dto.py
│   │   │       ├── question_dto.py
│   │   │       └── progress_dto.py
│   │   └── mappers/               # DTO Mappers
│   │       ├── __init__.py
│   │       ├── user_mapper.py
│   │       ├── question_mapper.py
│   │       └── progress_mapper.py
│   │
│   ├── infrastructure/            # Infrastructure Layer
│   │   ├── __init__.py
│   │   ├── persistence/           # Database Implementation
│   │   │   ├── __init__.py
│   │   │   ├── models/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── user_model.py
│   │   │   │   ├── question_model.py
│   │   │   │   ├── learning_model.py
│   │   │   │   └── content_model.py
│   │   │   ├── repositories/      # Repository Implementations
│   │   │   │   ├── __init__.py
│   │   │   │   ├── django_user_repository.py
│   │   │   │   ├── django_question_repository.py
│   │   │   │   └── django_progress_repository.py
│   │   │   └── migrations/
│   │   ├── cache/                 # Cache Implementation
│   │   │   ├── __init__.py
│   │   │   ├── redis_cache.py
│   │   │   ├── memory_cache.py
│   │   │   └── cache_manager.py
│   │   ├── queue/                 # Queue Implementation
│   │   │   ├── __init__.py
│   │   │   ├── celery_config.py
│   │   │   └── tasks/
│   │   │       ├── __init__.py
│   │   │       ├── import_tasks.py
│   │   │       └── analytics_tasks.py
│   │   ├── external/              # External Services
│   │   │   ├── __init__.py
│   │   │   ├── ai_service.py     # Phase 2
│   │   │   └── storage_service.py
│   │   └── importers/             # Data Importers
│   │       ├── __init__.py
│   │       ├── base_importer.py
│   │       ├── json_importer.py
│   │       └── bulk_importer.py
│   │
│   ├── interfaces/                # Interface Layer (API)
│   │   ├── __init__.py
│   │   ├── api/                   # FastAPI
│   │   │   ├── __init__.py
│   │   │   ├── main.py
│   │   │   ├── dependencies.py
│   │   │   ├── middleware/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── auth.py
│   │   │   │   └── cors.py
│   │   │   └── v1/
│   │   │       ├── __init__.py
│   │   │       ├── auth.py
│   │   │       ├── learning.py
│   │   │       ├── content.py
│   │   │       └── progress.py
│   │   ├── rest/                  # Django REST Framework
│   │   │   ├── __init__.py
│   │   │   ├── serializers/
│   │   │   ├── views/
│   │   │   └── urls.py
│   │   └── graphql/               # Future GraphQL support
│   │       └── __init__.py
│   │
│   └── shared/                    # Shared Utilities
│       ├── __init__.py
│       ├── dependency_injection.py
│       ├── event_bus.py
│       ├── exceptions.py
│       ├── validators.py
│       └── utils.py
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
├── scripts/
│   ├── import_questions.py
│   └── setup_dev.sh
│
├── requirements/
│   ├── base.txt
│   ├── development.txt
│   └── production.txt
│
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
│
└── manage.py
```

## 🗄️ Database Schema

### Core Tables

```sql
-- Content Hierarchy
CREATE TABLE topics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    order_index INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE subtopics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    topic_id UUID REFERENCES topics(id) ON DELETE CASCADE,
    code VARCHAR(100) NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    order_index INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(topic_id, code)
);

CREATE TABLE leaves (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subtopic_id UUID REFERENCES subtopics(id) ON DELETE CASCADE,
    code VARCHAR(100) NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    order_index INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(subtopic_id, code)
);

CREATE TABLE facets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    leaf_id UUID REFERENCES leaves(id) ON DELETE CASCADE,
    code VARCHAR(100) NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    order_index INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(leaf_id, code)
);

-- Questions
CREATE TABLE questions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    facet_id UUID REFERENCES facets(id) ON DELETE CASCADE,
    external_id VARCHAR(255) UNIQUE NOT NULL, -- from JSON
    type VARCHAR(20) NOT NULL CHECK (type IN ('mcq', 'theory', 'scenario')),
    question TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    difficulty_level INTEGER DEFAULT 3, -- 1-5 scale
    estimated_time_seconds INTEGER,
    tags TEXT[],
    source VARCHAR(50) DEFAULT 'hard_resource', -- Phase 1: hard_resource
    source_metadata JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_questions_facet (facet_id),
    INDEX idx_questions_type (type),
    INDEX idx_questions_difficulty (difficulty_level)
);

-- MCQ Options
CREATE TABLE mcq_options (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    question_id UUID REFERENCES questions(id) ON DELETE CASCADE,
    option_key VARCHAR(10) NOT NULL, -- A, B, C, D
    option_text TEXT NOT NULL,
    is_correct BOOLEAN DEFAULT false,
    explanation TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(question_id, option_key)
);

-- Users
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    preferences JSONB DEFAULT '{}',
    learning_settings JSONB DEFAULT '{}', -- Anki-like settings
    is_active BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP
);

-- Learning Sessions
CREATE TABLE learning_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    facet_id UUID REFERENCES facets(id),
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP,
    total_questions INTEGER DEFAULT 0,
    correct_answers INTEGER DEFAULT 0,
    session_metadata JSONB DEFAULT '{}',
    INDEX idx_sessions_user (user_id),
    INDEX idx_sessions_facet (facet_id)
);

-- User Responses (Learning History)
CREATE TABLE user_responses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    question_id UUID REFERENCES questions(id) ON DELETE CASCADE,
    session_id UUID REFERENCES learning_sessions(id) ON DELETE CASCADE,
    response_text TEXT, -- For theory/scenario
    selected_option VARCHAR(10), -- For MCQ
    is_correct BOOLEAN,
    difficulty_rating INTEGER CHECK (difficulty_rating IN (1, 2, 3, 4)), -- Easy, Medium, Hard, Very Hard
    time_spent_seconds INTEGER,
    confidence_level INTEGER CHECK (confidence_level BETWEEN 1 AND 5),
    response_metadata JSONB DEFAULT '{}', -- For Phase 2 AI analysis
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_responses_user_question (user_id, question_id),
    INDEX idx_responses_session (session_id)
);

-- Spaced Repetition Data (Anki-like)
CREATE TABLE spaced_repetition_cards (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    question_id UUID REFERENCES questions(id) ON DELETE CASCADE,
    ease_factor DECIMAL(3,2) DEFAULT 2.5, -- Anki's ease factor
    interval_days INTEGER DEFAULT 1,
    repetitions INTEGER DEFAULT 0,
    last_reviewed_at TIMESTAMP,
    next_review_at TIMESTAMP,
    total_reviews INTEGER DEFAULT 0,
    total_correct INTEGER DEFAULT 0,
    average_time_seconds INTEGER,
    card_state VARCHAR(20) DEFAULT 'new', -- new, learning, review, relearning
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, question_id),
    INDEX idx_cards_next_review (user_id, next_review_at),
    INDEX idx_cards_state (card_state)
);

-- User Progress Tracking
CREATE TABLE user_progress (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    facet_id UUID REFERENCES facets(id) ON DELETE CASCADE,
    total_questions INTEGER DEFAULT 0,
    completed_questions INTEGER DEFAULT 0,
    mastery_score DECIMAL(5,2) DEFAULT 0.0, -- 0-100
    last_activity_at TIMESTAMP,
    streak_days INTEGER DEFAULT 0,
    total_time_spent_seconds INTEGER DEFAULT 0,
    progress_metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, facet_id),
    INDEX idx_progress_user (user_id)
);

-- Analytics Events (For Phase 2 AI)
CREATE TABLE learning_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL,
    event_data JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_events_user_type (user_id, event_type),
    INDEX idx_events_created (created_at)
);
```

## 🔧 Domain Models

### Core Entities

```python
# domain/entities/question.py
from dataclasses import dataclass
from typing import Optional, Dict, List, Any
from enum import Enum
from datetime import datetime
import uuid

class QuestionType(Enum):
    MCQ = "mcq"
    THEORY = "theory"
    SCENARIO = "scenario"

class DifficultyLevel(Enum):
    VERY_EASY = 1
    EASY = 2
    MEDIUM = 3
    HARD = 4
    VERY_HARD = 5

class QuestionSource(Enum):
    HARD_RESOURCE = "hard_resource"  # Phase 1
    USER_GENERATED = "user_generated"  # Phase 2
    AI_GENERATED = "ai_generated"  # Phase 2
    ADMIN_IMPORTED = "admin_imported"  # Phase 2

@dataclass
class Question:
    id: uuid.UUID
    external_id: str
    facet_id: uuid.UUID
    type: QuestionType
    question_text: str
    difficulty_level: DifficultyLevel
    source: QuestionSource
    metadata: Dict[str, Any]
    tags: List[str]
    created_at: datetime
    updated_at: datetime
    
    # MCQ specific
    options: Optional[Dict[str, str]] = None
    correct_answer: Optional[str] = None
    explanation: Optional[str] = None
    
    def is_mcq(self) -> bool:
        return self.type == QuestionType.MCQ
    
    def validate(self) -> bool:
        if self.is_mcq():
            return bool(self.options and self.correct_answer)
        return True

# domain/entities/learning_session.py
@dataclass
class SpacedRepetitionCard:
    """Anki-like spaced repetition card"""
    id: uuid.UUID
    user_id: uuid.UUID
    question_id: uuid.UUID
    ease_factor: float = 2.5
    interval_days: int = 1
    repetitions: int = 0
    last_reviewed_at: Optional[datetime] = None
    next_review_at: Optional[datetime] = None
    card_state: str = "new"  # new, learning, review, relearning
    
    def calculate_next_review(self, difficulty_rating: int) -> datetime:
        """
        Calculate next review based on SuperMemo SM-2 algorithm
        difficulty_rating: 1 (Easy), 2 (Medium), 3 (Hard), 4 (Very Hard)
        """
        # Simplified SM-2 implementation
        if self.card_state == "new":
            if difficulty_rating == 1:
                self.interval_days = 4
            elif difficulty_rating == 2:
                self.interval_days = 2
            elif difficulty_rating == 3:
                self.interval_days = 1
            else:
                self.interval_days = 0  # Review again today
            self.card_state = "learning"
        else:
            # Update ease factor
            self.ease_factor = max(1.3, self.ease_factor + (0.1 - (4 - difficulty_rating) * 0.08))
            
            if difficulty_rating == 4:  # Very Hard - reset
                self.interval_days = 1
                self.card_state = "relearning"
            else:
                self.interval_days = int(self.interval_days * self.ease_factor)
                self.card_state = "review"
        
        self.repetitions += 1
        self.last_reviewed_at = datetime.now()
        self.next_review_at = datetime.now() + timedelta(days=self.interval_days)
        return self.next_review_at

# domain/entities/content_hierarchy.py
@dataclass
class ContentHierarchy:
    """Represents the learning content structure"""
    id: uuid.UUID
    code: str
    name: str
    level: str  # topic, subtopic, leaf, facet
    parent_id: Optional[uuid.UUID]
    children: List['ContentHierarchy']
    order_index: int
    is_active: bool
    
    def get_full_path(self) -> str:
        """Returns full path like: backend_nodejs__api__protocols__graphql"""
        # Implementation to build full path
        pass
```

## 🔄 Application Services

### Use Cases Implementation

```python
# application/use_cases/learning/get_next_question.py
from typing import Optional
from datetime import datetime
from domain.repositories import QuestionRepository, SpacedRepetitionRepository
from domain.entities import Question, SpacedRepetitionCard
from application.dto.request import GetNextQuestionRequest
from application.dto.response import QuestionResponse

class GetNextQuestionUseCase:
    def __init__(
        self,
        question_repo: QuestionRepository,
        sr_repo: SpacedRepetitionRepository
    ):
        self.question_repo = question_repo
        self.sr_repo = sr_repo
    
    async def execute(self, request: GetNextQuestionRequest) -> Optional[QuestionResponse]:
        """
        Get next question based on spaced repetition algorithm
        Priority:
        1. Overdue cards (next_review_at < now)
        2. New cards (never reviewed)
        3. Cards due for review today
        """
        user_id = request.user_id
        facet_id = request.facet_id
        
        # Get overdue cards first
        overdue_cards = await self.sr_repo.get_overdue_cards(
            user_id=user_id,
            facet_id=facet_id,
            limit=1
        )
        
        if overdue_cards:
            question = await self.question_repo.get_by_id(overdue_cards[0].question_id)
            return QuestionResponse.from_entity(question, overdue_cards[0])
        
        # Get new questions
        new_questions = await self.question_repo.get_unanswered_questions(
            user_id=user_id,
            facet_id=facet_id,
            limit=1
        )
        
        if new_questions:
            # Create new card
            card = SpacedRepetitionCard(
                user_id=user_id,
                question_id=new_questions[0].id,
                card_state="new"
            )
            await self.sr_repo.save(card)
            return QuestionResponse.from_entity(new_questions[0], card)
        
        # Get cards due today
        due_cards = await self.sr_repo.get_due_cards(
            user_id=user_id,
            facet_id=facet_id,
            due_date=datetime.now(),
            limit=1
        )
        
        if due_cards:
            question = await self.question_repo.get_by_id(due_cards[0].question_id)
            return QuestionResponse.from_entity(question, due_cards[0])
        
        return None

# application/use_cases/content/import_questions.py
from typing import List, Dict, Any
import json
from pathlib import Path
from domain.entities import Question, QuestionType, QuestionSource
from domain.repositories import QuestionRepository, ContentHierarchyRepository
from infrastructure.importers import JsonQuestionImporter

class ImportQuestionsUseCase:
    def __init__(
        self,
        question_repo: QuestionRepository,
        content_repo: ContentHierarchyRepository,
        importer: JsonQuestionImporter
    ):
        self.question_repo = question_repo
        self.content_repo = content_repo
        self.importer = importer
    
    async def execute(self, file_path: Path) -> Dict[str, Any]:
        """Import questions from JSON file"""
        # Parse filename to extract hierarchy
        # Example: backend_node_js__api__protocols__graphql.json
        filename = file_path.stem
        parts = filename.split("__")
        
        if len(parts) != 4:
            raise ValueError(f"Invalid filename format: {filename}")
        
        topic_code, subtopic_code, leaf_code, facet_code = parts
        
        # Ensure hierarchy exists
        facet = await self.content_repo.ensure_hierarchy(
            topic_code=topic_code,
            subtopic_code=subtopic_code,
            leaf_code=leaf_code,
            facet_code=facet_code
        )
        
        # Import questions
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        imported_count = 0
        skipped_count = 0
        errors = []
        
        for item in data:
            try:
                question = self.importer.parse_question(item, facet.id)
                
                # Check if question already exists
                existing = await self.question_repo.get_by_external_id(item['id'])
                if existing:
                    skipped_count += 1
                    continue
                
                await self.question_repo.save(question)
                imported_count += 1
                
            except Exception as e:
                errors.append({
                    'question_id': item.get('id'),
                    'error': str(e)
                })
        
        return {
            'imported': imported_count,
            'skipped': skipped_count,
            'errors': errors,
            'facet': facet_code
        }
```

## 🎯 FastAPI Interface

```python
# interfaces/api/main.py
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from .dependencies import get_container
from .v1 import auth, learning, content, progress

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    container = get_container()
    await container.init_resources()
    yield
    # Shutdown
    await container.shutdown_resources()

app = FastAPI(
    title="Learning Platform API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(learning.router, prefix="/api/v1/learning", tags=["learning"])
app.include_router(content.router, prefix="/api/v1/content", tags=["content"])
app.include_router(progress.router, prefix="/api/v1/progress", tags=["progress"])

# interfaces/api/v1/learning.py
from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from application.use_cases.learning import (
    GetNextQuestionUseCase,
    SubmitAnswerUseCase,
    StartLearningSessionUseCase
)
from application.dto.request import (
    GetNextQuestionRequest,
    SubmitAnswerRequest,
    StartSessionRequest
)
from ..dependencies import get_current_user, get_use_case

router = APIRouter()

@router.post("/sessions/start")
async def start_session(
    request: StartSessionRequest,
    user = Depends(get_current_user),
    use_case: StartLearningSessionUseCase = Depends(get_use_case(StartLearningSessionUseCase))
):
    request.user_id = user.id
    session = await use_case.execute(request)
    return session

@router.get("/questions/next")
async def get_next_question(
    facet_id: str,
    user = Depends(get_current_user),
    use_case: GetNextQuestionUseCase = Depends(get_use_case(GetNextQuestionUseCase))
):
    request = GetNextQuestionRequest(
        user_id=user.id,
        facet_id=facet_id
    )
    question = await use_case.execute(request)
    if not question:
        raise HTTPException(404, "No questions available")
    return question

@router.post("/questions/{question_id}/answer")
async def submit_answer(
    question_id: str,
    request: SubmitAnswerRequest,
    user = Depends(get_current_user),
    use_case: SubmitAnswerUseCase = Depends(get_use_case(SubmitAnswerUseCase))
):
    request.user_id = user.id
    request.question_id = question_id
    result = await use_case.execute(request)
    return result
```

## 🔌 Dependency Injection

```python
# shared/dependency_injection.py
from dependency_injector import containers, providers
from infrastructure.persistence.repositories import (
    DjangoUserRepository,
    DjangoQuestionRepository,
    DjangoProgressRepository
)
from infrastructure.cache import RedisCacheManager, MemoryCacheManager
from application.use_cases.learning import (
    GetNextQuestionUseCase,
    SubmitAnswerUseCase
)

class Container(containers.DeclarativeContainer):
    config = providers.Configuration()
    
    # Cache providers
    memory_cache = providers.Singleton(
        MemoryCacheManager,
        max_size=config.cache.memory_max_size
    )
    
    redis_cache = providers.Singleton(
        RedisCacheManager,
        host=config.redis.host,
        port=config.redis.port,
        db=config.redis.db
    )
    
    cache_manager = providers.Singleton(
        CacheManager,
        memory_cache=memory_cache,
        redis_cache=redis_cache
    )
    
    # Repository providers
    user_repository = providers.Singleton(
        DjangoUserRepository,
        cache=cache_manager
    )
    
    question_repository = providers.Singleton(
        DjangoQuestionRepository,
        cache=cache_manager
    )
    
    progress_repository = providers.Singleton(
        DjangoProgressRepository,
        cache=cache_manager
    )
    
    spaced_repetition_repository = providers.Singleton(
        DjangoSpacedRepetitionRepository,
        cache=cache_manager
    )
    
    # Use case providers
    get_next_question_use_case = providers.Factory(
        GetNextQuestionUseCase,
        question_repo=question_repository,
        sr_repo=spaced_repetition_repository
    )
    
    submit_answer_use_case = providers.Factory(
        SubmitAnswerUseCase,
        question_repo=question_repository,
        sr_repo=spaced_repetition_repository,
        progress_repo=progress_repository
    )

# interfaces/api/dependencies.py
from functools import lru_cache
from typing import Type, TypeVar
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from shared.dependency_injection import Container
import jwt

security = HTTPBearer()
T = TypeVar('T')

@lru_cache()
def get_container() -> Container:
    container = Container()
    container.config.from_yaml('config.yaml')
    return container

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    container: Container = Depends(get_container)
):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, container.config.jwt.secret(), algorithms=["HS256"])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        
        user_repo = container.user_repository()
        user = await user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

def get_use_case(use_case_class: Type[T]) -> T:
    def _get_use_case(container: Container = Depends(get_container)) -> T:
        provider_name = f"{use_case_class.__name__[0].lower()}{use_case_class.__name__[1:]}"
        return getattr(container, provider_name)()
    return _get_use_case
```

## 🚀 Infrastructure Implementation

### Cache Layer

```python
# infrastructure/cache/cache_manager.py
from typing import Optional, Any, List
from abc import ABC, abstractmethod
import json
import hashlib
from datetime import timedelta

class CacheStrategy(ABC):
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        pass
    
    @abstractmethod
    async def delete(self, key: str):
        pass
    
    @abstractmethod
    async def clear_pattern(self, pattern: str):
        pass

class MemoryCacheManager(CacheStrategy):
    def __init__(self, max_size: int = 1000):
        from cachetools import TTLCache
        self.cache = TTLCache(maxsize=max_size, ttl=300)  # 5 min default
    
    async def get(self, key: str) -> Optional[Any]:
        return self.cache.get(key)
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        if ttl:
            # Create new cache with specific TTL
            self.cache[key] = value
        else:
            self.cache[key] = value
    
    async def delete(self, key: str):
        self.cache.pop(key, None)
    
    async def clear_pattern(self, pattern: str):
        keys_to_delete = [k for k in self.cache.keys() if pattern in k]
        for key in keys_to_delete:
            self.cache.pop(key, None)

class RedisCacheManager(CacheStrategy):
    def __init__(self, host: str, port: int, db: int):
        import redis.asyncio as redis
        self.redis = redis.Redis(
            host=host, 
            port=port, 
            db=db,
            decode_responses=True
        )
    
    async def get(self, key: str) -> Optional[Any]:
        value = await self.redis.get(key)
        if value:
            return json.loads(value)
        return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        serialized = json.dumps(value)
        if ttl:
            await self.redis.setex(key, ttl, serialized)
        else:
            await self.redis.set(key, serialized)
    
    async def delete(self, key: str):
        await self.redis.delete(key)
    
    async def clear_pattern(self, pattern: str):
        cursor = 0
        while True:
            cursor, keys = await self.redis.scan(
                cursor, match=f"*{pattern}*", count=100
            )
            if keys:
                await self.redis.delete(*keys)
            if cursor == 0:
                break

class CacheManager:
    """Multi-layer cache manager"""
    def __init__(self, memory_cache: MemoryCacheManager, redis_cache: RedisCacheManager):
        self.memory = memory_cache
        self.redis = redis_cache
    
    def generate_key(self, prefix: str, **kwargs) -> str:
        """Generate cache key from prefix and parameters"""
        params = json.dumps(kwargs, sort_keys=True)
        hash_digest = hashlib.md5(params.encode()).hexdigest()[:8]
        return f"{prefix}:{hash_digest}"
    
    async def get(self, key: str) -> Optional[Any]:
        # Check memory first
        value = await self.memory.get(key)
        if value:
            return value
        
        # Check Redis
        value = await self.redis.get(key)
        if value:
            # Store in memory for next time
            await self.memory.set(key, value)
            return value
        
        return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        # Set in both layers
        await self.memory.set(key, value, ttl)
        await self.redis.set(key, value, ttl)
    
    async def delete(self, key: str):
        await self.memory.delete(key)
        await self.redis.delete(key)
    
    async def invalidate_pattern(self, pattern: str):
        """Invalidate all keys matching pattern"""
        await self.memory.clear_pattern(pattern)
        await self.redis.clear_pattern(pattern)
```

### Repository Implementation

```python
# infrastructure/persistence/repositories/django_question_repository.py
from typing import List, Optional
from uuid import UUID
from domain.repositories import QuestionRepository
from domain.entities import Question, QuestionType
from infrastructure.persistence.models import QuestionModel, MCQOptionModel
from infrastructure.cache import CacheManager

class DjangoQuestionRepository(QuestionRepository):
    def __init__(self, cache: CacheManager):
        self.cache = cache
    
    async def get_by_id(self, question_id: UUID) -> Optional[Question]:
        cache_key = self.cache.generate_key("question", id=str(question_id))
        
        # Check cache
        cached = await self.cache.get(cache_key)
        if cached:
            return Question(**cached)
        
        # Get from DB
        try:
            question_model = await QuestionModel.objects.select_related(
                'facet', 'mcq_options'
            ).aget(id=question_id)
            
            question = self._model_to_entity(question_model)
            
            # Cache it
            await self.cache.set(cache_key, question.__dict__, ttl=3600)
            
            return question
        except QuestionModel.DoesNotExist:
            return None
    
    async def get_by_external_id(self, external_id: str) -> Optional[Question]:
        try:
            question_model = await QuestionModel.objects.select_related(
                'facet', 'mcq_options'
            ).aget(external_id=external_id)
            return self._model_to_entity(question_model)
        except QuestionModel.DoesNotExist:
            return None
    
    async def get_unanswered_questions(
        self, 
        user_id: UUID, 
        facet_id: UUID, 
        limit: int = 10
    ) -> List[Question]:
        # Get questions not in user_responses for this user
        query = """
            SELECT q.* FROM questions q
            WHERE q.facet_id = %s
            AND q.is_active = true
            AND NOT EXISTS (
                SELECT 1 FROM user_responses ur
                WHERE ur.question_id = q.id
                AND ur.user_id = %s
            )
            ORDER BY q.order_index, q.created_at
            LIMIT %s
        """
        
        question_models = await QuestionModel.objects.raw(
            query, [str(facet_id), str(user_id), limit]
        ).afetch()
        
        return [self._model_to_entity(q) for q in question_models]
    
    async def save(self, question: Question) -> Question:
        # Convert entity to model
        question_model, created = await QuestionModel.objects.aupdate_or_create(
            external_id=question.external_id,
            defaults={
                'facet_id': question.facet_id,
                'type': question.type.value,
                'question': question.question_text,
                'difficulty_level': question.difficulty_level.value,
                'metadata': question.metadata,
                'tags': question.tags,
                'source': question.source.value
            }
        )
        
        # Save MCQ options if applicable
        if question.is_mcq() and question.options:
            for key, text in question.options.items():
                await MCQOptionModel.objects.aupdate_or_create(
                    question_id=question_model.id,
                    option_key=key,
                    defaults={
                        'option_text': text,
                        'is_correct': key == question.correct_answer,
                        'explanation': question.explanation if key == question.correct_answer else None
                    }
                )
        
        # Invalidate cache
        await self.cache.invalidate_pattern(f"question:{question_model.id}")
        await self.cache.invalidate_pattern(f"facet:{question.facet_id}")
        
        return self._model_to_entity(question_model)
    
    def _model_to_entity(self, model: QuestionModel) -> Question:
        options = None
        correct_answer = None
        explanation = None
        
        if model.type == 'mcq':
            options = {
                opt.option_key: opt.option_text 
                for opt in model.mcq_options.all()
            }
            correct_opt = next(
                (opt for opt in model.mcq_options.all() if opt.is_correct), 
                None
            )
            if correct_opt:
                correct_answer = correct_opt.option_key
                explanation = correct_opt.explanation
        
        return Question(
            id=model.id,
            external_id=model.external_id,
            facet_id=model.facet_id,
            type=QuestionType(model.type),
            question_text=model.question,
            difficulty_level=DifficultyLevel(model.difficulty_level),
            source=QuestionSource(model.source),
            metadata=model.metadata,
            tags=model.tags,
            created_at=model.created_at,
            updated_at=model.updated_at,
            options=options,
            correct_answer=correct_answer,
            explanation=explanation
        )
```

### Celery Tasks

```python
# infrastructure/queue/tasks/import_tasks.py
from celery import shared_task
from pathlib import Path
from typing import Dict, Any
import logging
from application.use_cases.content import ImportQuestionsUseCase
from shared.dependency_injection import Container

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def import_questions_batch(self, file_paths: List[str]) -> Dict[str, Any]:
    """Import multiple question files in batch"""
    container = Container()
    container.config.from_yaml('config.yaml')
    
    use_case = container.import_questions_use_case()
    
    results = {
        'total_files': len(file_paths),
        'successful': 0,
        'failed': 0,
        'details': []
    }
    
    for file_path in file_paths:
        try:
            path = Path(file_path)
            result = use_case.execute(path)
            results['successful'] += 1
            results['details'].append({
                'file': file_path,
                'status': 'success',
                'imported': result['imported'],
                'skipped': result['skipped']
            })
            
            # Log progress
            logger.info(f"Imported {file_path}: {result['imported']} questions")
            
            # Update task state for monitoring
            self.update_state(
                state='PROGRESS',
                meta={
                    'current': results['successful'] + results['failed'],
                    'total': results['total_files']
                }
            )
            
        except Exception as e:
            results['failed'] += 1
            results['details'].append({
                'file': file_path,
                'status': 'failed',
                'error': str(e)
            })
            logger.error(f"Failed to import {file_path}: {e}")
    
    return results

@shared_task
def calculate_user_analytics(user_id: str):
    """Calculate and cache user learning analytics"""
    # Implementation for analytics calculation
    pass

@shared_task
def generate_daily_review_cards():
    """Generate daily review cards for all active users"""
    # Implementation for daily card generation
    pass
```

## 📝 Import Script

```python
# scripts/import_questions.py
#!/usr/bin/env python
import os
import sys
import django
from pathlib import Path
import asyncio
from typing import List

# Setup Django
sys.path.append(str(Path(__file__).parent.parent / 'src'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.development')
django.setup()

from infrastructure.queue.tasks import import_questions_batch
from infrastructure.persistence.models import FacetModel

async def main():
    """Import all JSON files from data directory"""
    data_dir = Path("data/questions")
    json_files = list(data_dir.glob("*.json"))
    
    print(f"Found {len(json_files)} JSON files to import")
    
    # Group files by batch size
    batch_size = 50
    batches = [
        json_files[i:i + batch_size] 
        for i in range(0, len(json_files), batch_size)
    ]
    
    # Submit batches to Celery
    tasks = []
    for batch in batches:
        file_paths = [str(f) for f in batch]
        task = import_questions_batch.delay(file_paths)
        tasks.append(task)
        print(f"Submitted batch with {len(file_paths)} files")
    
    # Wait for completion
    print("Waiting for import to complete...")
    for task in tasks:
        result = task.get(timeout=300)  # 5 min timeout
        print(f"Batch completed: {result['successful']}/{result['total_files']} successful")
    
    print("Import completed!")

if __name__ == "__main__":
    asyncio.run(main())
```

## 🐳 Docker Configuration

```yaml
# docker/docker-compose.yml
version: '3.8'

services:
  mariadb:
    image: mariadb:10.11
    environment:
      MYSQL_ROOT_PASSWORD: rootpass
      MYSQL_DATABASE: learning_platform
      MYSQL_USER: learning_user
      MYSQL_PASSWORD: learning_pass
    volumes:
      - mariadb_data:/var/lib/mysql
    ports:
      - "3306:3306"
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
      timeout: 5s
      retries: 10

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      timeout: 5s
      retries: 10

  backend:
    build:
      context: ..
      dockerfile: docker/Dockerfile
    environment:
      - DATABASE_URL=mysql://learning_user:learning_pass@mariadb:3306/learning_platform
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/1
      - SECRET_KEY=your-secret-key-here
      - DEBUG=True
    volumes:
      - ../src:/app/src
      - ../data:/app/data
    ports:
      - "8000:8000"  # Django
      - "8001:8001"  # FastAPI
    depends_on:
      mariadb:
        condition: service_healthy
      redis:
        condition: service_healthy
    command: >
      sh -c "
        python manage.py migrate &&
        python -m uvicorn interfaces.api.main:app --host 0.0.0.0 --port 8001 --reload &
        python manage.py runserver 0.0.0.0:8000
      "

  celery:
    build:
      context: ..
      dockerfile: docker/Dockerfile
    environment:
      - DATABASE_URL=mysql://learning_user:learning_pass@mariadb:3306/learning_platform
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/1
    volumes:
      - ../src:/app/src
      - ../data:/app/data
    depends_on:
      - mariadb
      - redis
    command: celery -A infrastructure.queue.celery_config worker -l info

  celery-beat:
    build:
      context: ..
      dockerfile: docker/Dockerfile
    environment:
      - DATABASE_URL=mysql://learning_user:learning_pass@mariadb:3306/learning_platform
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/1
    volumes:
      - ../src:/app/src
    depends_on:
      - mariadb
      - redis
    command: celery -A infrastructure.queue.celery_config beat -l info

volumes:
  mariadb_data:
  redis_data:

# docker/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements/base.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY src /app/src
COPY manage.py /app/

ENV PYTHONPATH=/app/src:$PYTHONPATH

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
```

## 📦 Requirements

```txt
# requirements/base.txt
# Django
Django==5.0.1
djangorestframework==3.14.0
django-cors-headers==4.3.1
django-extensions==3.2.3

# FastAPI
fastapi==0.109.0
uvicorn[standard]==0.27.0
python-multipart==0.0.6

# Database
mysqlclient==2.2.1
django-environ==0.11.2

# Cache
redis==5.0.1
hiredis==2.3.2
cachetools==5.3.2

# Queue
celery==5.3.4
celery[redis]==5.3.4
django-celery-beat==2.5.0
django-celery-results==2.5.1

# Auth
PyJWT==2.8.0
passlib[bcrypt]==1.7.4
python-jose[cryptography]==3.3.0

# Dependency Injection
dependency-injector==4.41.0

# Utilities
pydantic==2.5.3
python-dateutil==2.8.2
pytz==2023.3

# Development
ipython==8.19.0
black==23.12.1
pylint==3.0.3
pytest==7.4.4
pytest-django==4.7.0
pytest-asyncio==0.21.1

# requirements/development.txt
-r base.txt
django-debug-toolbar==4.2.0
pytest-cov==4.1.0
factory-boy==3.3.0
faker==22.0.0

# requirements/production.txt
-r base.txt
gunicorn==21.2.0
sentry-sdk==1.39.1
django-storages[boto3]==1.14.2
```

## 🎯 Phase 2 & 3 Extension Points

### AI Integration (Phase 2)
- Add AI service in `infrastructure/external/ai_service.py`
- Implement answer evaluation use cases
- Add chat functionality endpoints
- Store AI interactions in `learning_events` table

### Voice Integration (Phase 3)
- Add speech-to-text service
- Implement WebSocket for real-time transcription
- Add voice response endpoints
- Store voice metrics in analytics

### Scalability Considerations
1. **Horizontal Scaling**: Stateless services, Redis session management
2. **Database Sharding**: Partition by user_id for large scale
3. **Caching Strategy**: Multi-layer caching with TTL management
4. **Queue Processing**: Celery for async tasks
5. **Event Sourcing**: Store all learning events for AI analysis
6. **API Versioning**: Clear version strategy for backward compatibility

## 🚀 Getting Started

```bash
# Clone repository
git clone <repository>
cd learning-platform-backend

# Setup environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -r requirements/development.txt

# Start services
docker-compose up -d mariadb redis

# Run migrations
python manage.py makemigrations
python manage.py migrate

# Import questions
python scripts/import_questions.py

# Start servers
# Terminal 1: Django
python manage.py runserver

# Terminal 2: FastAPI
uvicorn interfaces.api.main:app --reload --port 8001

# Terminal 3: Celery
celery -A infrastructure.queue.celery_config worker -l info

# Terminal 4: Celery Beat
celery -A infrastructure.queue.celery_config beat -l info
```