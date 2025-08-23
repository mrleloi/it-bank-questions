"""Dependency injection container."""

from dependency_injector import containers, providers
from django.conf import settings

from infrastructure.cache import CacheManager, RedisCache, MemoryCache
from infrastructure.persistence.repositories import *
from infrastructure.services import *
from domain.services import *
from application.use_cases.auth import *
from application.use_cases.learning import *
from application.use_cases.content import *
from application.use_cases.progress import *
from application.use_cases.analytics import *


class Container(containers.DeclarativeContainer):
    """Main DI container."""

    config = providers.Configuration()

    # Cache providers
    memory_cache = providers.Singleton(
        MemoryCache,
        max_size=config.cache.memory_max_size
    )

    redis_cache = providers.Singleton(
        RedisCache,
        host=config.redis.host,
        port=config.redis.port,
        db=config.redis.db,
        password=config.redis.password
    )

    cache_manager = providers.Singleton(
        CacheManager,
        memory_cache=memory_cache,
        redis_cache=redis_cache
    )

    # Repository providers
    user_repository = providers.Singleton(
        DjangoUserRepository,
        cache_manager=cache_manager
    )

    question_repository = providers.Singleton(
        DjangoQuestionRepository,
        cache_manager=cache_manager
    )

    session_repository = providers.Singleton(
        DjangoSessionRepository,
        cache_manager=cache_manager
    )

    spaced_repetition_repository = providers.Singleton(
        DjangoSpacedRepetitionRepository,
        cache_manager=cache_manager
    )

    progress_repository = providers.Singleton(
        DjangoProgressRepository,
        cache_manager=cache_manager
    )

    content_repository = providers.Singleton(
        DjangoContentRepository,
        cache_manager=cache_manager
    )

    event_repository = providers.Singleton(
        DjangoEventRepository,
        cache_manager=cache_manager
    )

    # Domain services
    spaced_repetition_service = providers.Factory(
        SpacedRepetitionService,
        card_repository=spaced_repetition_repository,
        question_repository=question_repository
    )

    learning_path_service = providers.Factory(
        LearningPathService,
        question_repo=question_repository,
        progress_repo=progress_repository,
        sr_repo=spaced_repetition_repository,
        content_repo=content_repository
    )

    achievement_service = providers.Factory(
        AchievementService,
        progress_repo=progress_repository,
        event_repo=event_repository
    )

    analytics_service = providers.Factory(
        AnalyticsService,
        event_repo=event_repository,
        session_repo=session_repository,
        progress_repo=progress_repository,
        question_repo=question_repository
    )

    # Application services
    email_service = providers.Singleton(
        DjangoEmailService,
        config=config.email
    )

    event_bus = providers.Singleton(
        DjangoEventBus
    )

    # Use cases - Authentication
    register_user_use_case = providers.Factory(
        RegisterUserUseCase,
        user_repository=user_repository,
        email_service=email_service,
        event_bus=event_bus
    )

    authenticate_user_use_case = providers.Factory(
        AuthenticateUserUseCase,
        user_repository=user_repository,
        event_bus=event_bus,
        auth_config=config.auth
    )

    # Use cases - Learning
    start_session_use_case = providers.Factory(
        StartLearningSessionUseCase,
        session_repository=session_repository,
        question_repository=question_repository,
        learning_path_service=learning_path_service,
        event_bus=event_bus
    )

    get_next_question_use_case = providers.Factory(
        GetNextQuestionUseCase,
        session_repository=session_repository,
        question_repository=question_repository,
        sr_repository=spaced_repetition_repository,
        sr_service=spaced_repetition_service
    )

    submit_answer_use_case = providers.Factory(
        SubmitAnswerUseCase,
        session_repository=session_repository,
        question_repository=question_repository,
        sr_repository=spaced_repetition_repository,
        progress_repository=progress_repository,
        event_repository=event_repository,
        sr_service=spaced_repetition_service,
        achievement_service=achievement_service,
        event_bus=event_bus
    )

    # Use cases - Content
    import_questions_use_case = providers.Factory(
        ImportQuestionsUseCase,
        question_repository=question_repository,
        content_repository=content_repository,
        content_service=providers.Factory(
            ContentHierarchyService,
            content_repo=content_repository,
            question_repo=question_repository,
            progress_repo=progress_repository
        )
    )

    # Use cases - Analytics
    get_user_analytics_use_case = providers.Factory(
        GetUserAnalyticsUseCase,
        analytics_service=analytics_service
    )

    # Initialize resources
    async def init_resources(self):
        """Initialize resources on startup."""
        # Test Redis connection
        if self.redis_cache():
            await self.redis_cache().redis.ping()

    async def shutdown_resources(self):
        """Cleanup resources on shutdown."""
        # Close Redis connection
        if self.redis_cache():
            await self.redis_cache().close()


def create_container() -> Container:
    """Create and configure container."""
    container = Container()

    # Load configuration
    container.config.from_dict({
        'cache': {
            'memory_max_size': 1000,
        },
        'redis': {
            'host': settings.REDIS_HOST,
            'port': settings.REDIS_PORT,
            'db': settings.REDIS_DB,
            'password': settings.REDIS_PASSWORD,
        },
        'auth': {
            'secret_key': settings.SECRET_KEY,
            'algorithm': 'HS256',
            'access_token_expire_minutes': 30,
            'refresh_token_expire_days': 7,
        },
        'email': {
            'host': settings.EMAIL_HOST,
            'port': settings.EMAIL_PORT,
            'user': settings.EMAIL_HOST_USER,
            'password': settings.EMAIL_HOST_PASSWORD,
        }
    })

    return container
