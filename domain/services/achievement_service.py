"""Achievement domain service."""

from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime

from ..entities import UserProgress, LearningEvent
from ..entities.learning_event import EventType
from ..repositories import ProgressRepository, EventRepository
from ..events import AchievementUnlockedEvent


class Achievement:
    """Achievement definition."""

    def __init__(
            self,
            name: str,
            display_name: str,
            description: str,
            points: int,
            icon: str,
            criteria: Dict[str, Any]
    ):
        self.name = name
        self.display_name = display_name
        self.description = description
        self.points = points
        self.icon = icon
        self.criteria = criteria


class AchievementService:
    """Service for managing achievements."""

    # Define all achievements
    ACHIEVEMENTS = [
        Achievement(
            name="first_question",
            display_name="First Step",
            description="Answer your first question",
            points=10,
            icon="🎯",
            criteria={"questions_answered": 1}
        ),
        Achievement(
            name="century_club",
            display_name="Century Club",
            description="Answer 100 questions",
            points=50,
            icon="💯",
            criteria={"questions_answered": 100}
        ),
        Achievement(
            name="thousand_answers",
            display_name="Thousand Answers",
            description="Answer 1000 questions",
            points=200,
            icon="🏆",
            criteria={"questions_answered": 1000}
        ),
        Achievement(
            name="week_warrior",
            display_name="Week Warrior",
            description="Maintain a 7-day streak",
            points=25,
            icon="🔥",
            criteria={"streak_days": 7}
        ),
        Achievement(
            name="monthly_master",
            display_name="Monthly Master",
            description="Maintain a 30-day streak",
            points=100,
            icon="🌟",
            criteria={"streak_days": 30}
        ),
        Achievement(
            name="perfect_session",
            display_name="Perfect Session",
            description="Complete a session with 100% accuracy",
            points=30,
            icon="✨",
            criteria={"session_accuracy": 100, "min_questions": 10}
        ),
        Achievement(
            name="speed_demon",
            display_name="Speed Demon",
            description="Answer 10 questions in under 5 minutes",
            points=40,
            icon="⚡",
            criteria={"questions_in_time": {"count": 10, "minutes": 5}}
        ),
        Achievement(
            name="night_owl",
            display_name="Night Owl",
            description="Study after midnight",
            points=15,
            icon="🦉",
            criteria={"study_time": "night"}
        ),
        Achievement(
            name="early_bird",
            display_name="Early Bird",
            description="Study before 6 AM",
            points=15,
            icon="🐦",
            criteria={"study_time": "early"}
        ),
        Achievement(
            name="facet_master",
            display_name="Facet Master",
            description="Master your first facet (80%+ mastery)",
            points=75,
            icon="🎓",
            criteria={"facets_mastered": 1}
        ),
        Achievement(
            name="topic_expert",
            display_name="Topic Expert",
            description="Complete all facets in a topic",
            points=150,
            icon="👨‍🎓",
            criteria={"topics_completed": 1}
        ),
        Achievement(
            name="polymath",
            display_name="Polymath",
            description="Study 5 different topics",
            points=100,
            icon="🧠",
            criteria={"unique_topics": 5}
        ),
    ]

    def __init__(
            self,
            progress_repo: ProgressRepository,
            event_repo: EventRepository
    ):
        self.progress_repo = progress_repo
        self.event_repo = event_repo
        self._achievements_map = {a.name: a for a in self.ACHIEVEMENTS}

    async def check_achievements(
            self,
            user_id: UUID,
            trigger_event: Optional[LearningEvent] = None
    ) -> List[Achievement]:
        """Check and unlock new achievements for user."""
        user_progress = await self.progress_repo.get_user_progress(user_id)
        unlocked = []

        for achievement in self.ACHIEVEMENTS:
            if achievement.name not in user_progress.achievements_unlocked:
                if await self._check_criteria(
                        achievement,
                        user_progress,
                        user_id,
                        trigger_event
                ):
                    # Unlock achievement
                    user_progress.achievements_unlocked.append(achievement.name)
                    user_progress.achievement_points += achievement.points
                    unlocked.append(achievement)

                    # Create achievement event
                    event = LearningEvent(
                        user_id=user_id,
                        event_type=EventType.ACHIEVEMENT_UNLOCKED,
                        event_data={
                            'achievement_name': achievement.name,
                            'display_name': achievement.display_name,
                            'points': achievement.points
                        }
                    )
                    await self.event_repo.save(event)

        # Save updated progress
        if unlocked:
            await self.progress_repo.save(user_progress)

        return unlocked

    async def get_user_achievements(
            self,
            user_id: UUID
    ) -> Dict[str, Any]:
        """Get user's achievement status."""
        user_progress = await self.progress_repo.get_user_progress(user_id)

        unlocked = []
        locked = []

        for achievement in self.ACHIEVEMENTS:
            achievement_data = {
                'name': achievement.name,
                'display_name': achievement.display_name,
                'description': achievement.description,
                'points': achievement.points,
                'icon': achievement.icon
            }

            if achievement.name in user_progress.achievements_unlocked:
                # Get unlock date from events
                events = await self.event_repo.get_user_events(
                    user_id,
                    event_type=EventType.ACHIEVEMENT_UNLOCKED
                )
                unlock_event = next(
                    (e for e in events
                     if e.event_data.get('achievement_name') == achievement.name),
                    None
                )
                if unlock_event:
                    achievement_data['unlocked_at'] = unlock_event.created_at.isoformat()

                unlocked.append(achievement_data)
            else:
                # Calculate progress towards achievement
                progress = await self._calculate_progress(
                    achievement,
                    user_progress,
                    user_id
                )
                achievement_data['progress'] = progress
                locked.append(achievement_data)

        return {
            'total_points': user_progress.achievement_points,
            'unlocked_count': len(unlocked),
            'total_count': len(self.ACHIEVEMENTS),
            'unlocked': unlocked,
            'locked': locked
        }

    async def get_leaderboard(
            self,
            limit: int = 10,
            timeframe: Optional[str] = None  # 'week', 'month', 'all'
    ) -> List[Dict[str, Any]]:
        """Get achievement points leaderboard."""
        # This would typically query a leaderboard-specific table/cache
        top_users = await self.progress_repo.get_top_learners(limit=limit)

        leaderboard = []
        for rank, user_data in enumerate(top_users, 1):
            leaderboard.append({
                'rank': rank,
                'user_id': user_data['user_id'],
                'username': user_data['username'],
                'points': user_data['achievement_points'],
                'achievements_count': len(user_data.get('achievements', []))
            })

        return leaderboard

    async def _check_criteria(
            self,
            achievement: Achievement,
            user_progress: UserProgress,
            user_id: UUID,
            trigger_event: Optional[LearningEvent]
    ) -> bool:
        """Check if achievement criteria are met."""
        criteria = achievement.criteria

        # Questions answered
        if 'questions_answered' in criteria:
            if user_progress.total_questions_answered < criteria['questions_answered']:
                return False

        # Streak days
        if 'streak_days' in criteria:
            max_streak = max(
                (p.current_streak_days for p in user_progress.facet_progresses.values()),
                default=0
            )
            if max_streak < criteria['streak_days']:
                return False

        # Session accuracy
        if 'session_accuracy' in criteria and trigger_event:
            if trigger_event.event_type == EventType.SESSION_COMPLETED:
                accuracy = trigger_event.event_data.get('accuracy_rate', 0)
                questions = trigger_event.event_data.get('total_questions', 0)
                min_questions = criteria.get('min_questions', 1)

                if accuracy < criteria['session_accuracy'] or questions < min_questions:
                    return False
            else:
                return False  # Can only check on session completion

        # Speed achievements
        if 'questions_in_time' in criteria and trigger_event:
            if trigger_event.event_type == EventType.SESSION_COMPLETED:
                questions = trigger_event.event_data.get('total_questions', 0)
                time_minutes = trigger_event.event_data.get('total_time_seconds', 0) / 60

                required = criteria['questions_in_time']
                if questions < required['count'] or time_minutes > required['minutes']:
                    return False
            else:
                return False

        # Study time achievements
        if 'study_time' in criteria and trigger_event:
            if trigger_event.event_type in [EventType.SESSION_STARTED, EventType.QUESTION_ANSWERED]:
                hour = datetime.now().hour

                if criteria['study_time'] == 'night' and not (0 <= hour < 5):
                    return False
                elif criteria['study_time'] == 'early' and not (4 <= hour < 6):
                    return False
            else:
                return False

        # Facets mastered
        if 'facets_mastered' in criteria:
            mastered_count = sum(
                1 for p in user_progress.facet_progresses.values()
                if p.is_mastered()
            )
            if mastered_count < criteria['facets_mastered']:
                return False

        # Additional complex criteria would be checked here

        return True

    async def _calculate_progress(
            self,
            achievement: Achievement,
            user_progress: UserProgress,
            user_id: UUID
    ) -> Dict[str, Any]:
        """Calculate progress towards an achievement."""
        criteria = achievement.criteria
        progress = {}

        if 'questions_answered' in criteria:
            current = user_progress.total_questions_answered
            target = criteria['questions_answered']
            progress['percentage'] = min(100, (current / target) * 100)
            progress['current'] = current
            progress['target'] = target

        elif 'streak_days' in criteria:
            max_streak = max(
                (p.current_streak_days for p in user_progress.facet_progresses.values()),
                default=0
            )
            target = criteria['streak_days']
            progress['percentage'] = min(100, (max_streak / target) * 100)
            progress['current'] = max_streak
            progress['target'] = target

        elif 'facets_mastered' in criteria:
            mastered_count = sum(
                1 for p in user_progress.facet_progresses.values()
                if p.is_mastered()
            )
            target = criteria['facets_mastered']
            progress['percentage'] = min(100, (mastered_count / target) * 100)
            progress['current'] = mastered_count
            progress['target'] = target

        else:
            progress['percentage'] = 0
            progress['description'] = "Complete specific action to unlock"

        return progress