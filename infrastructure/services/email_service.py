"""Email service implementation."""

import logging
from typing import Dict, Any, Optional
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings

from application.services import EmailService

logger = logging.getLogger(__name__)


class DjangoEmailService(EmailService):
    """Django implementation of EmailService."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@learning-platform.com')
        self.frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')

    async def send_verification_email(
            self,
            email: str,
            username: str,
            token: str
    ) -> bool:
        """Send email verification."""
        try:
            subject = 'Verify Your Email - Learning Platform'
            verification_url = f"{self.frontend_url}/verify-email?token={token}"
            
            # Create HTML content
            html_content = f"""
            <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px;">
                    <h2 style="color: #2c3e50;">Welcome to Learning Platform!</h2>
                    <p>Hi <strong>{username}</strong>,</p>
                    <p>Thank you for registering with Learning Platform. Please verify your email address by clicking the button below:</p>
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{verification_url}" 
                           style="background-color: #3498db; color: white; padding: 12px 30px; 
                                  text-decoration: none; border-radius: 5px; display: inline-block;">
                            Verify Email Address
                        </a>
                    </div>
                    <p>Or copy and paste this link in your browser:</p>
                    <p style="word-break: break-all; color: #7f8c8d;">{verification_url}</p>
                    <p><small>This link will expire in 7 days.</small></p>
                    <hr style="margin: 30px 0; border: 1px solid #ecf0f1;">
                    <p style="color: #7f8c8d; font-size: 12px;">
                        If you didn't create an account, please ignore this email.
                    </p>
                </div>
            </body>
            </html>
            """
            
            # Plain text version
            plain_content = f"""
            Hi {username},
            
            Thank you for registering with Learning Platform. 
            Please verify your email address by clicking this link:
            
            {verification_url}
            
            This link will expire in 7 days.
            
            If you didn't create an account, please ignore this email.
            """

            send_mail(
                subject=subject,
                message=plain_content,
                from_email=self.from_email,
                recipient_list=[email],
                html_message=html_content,
                fail_silently=False
            )
            
            logger.info(f"Verification email sent to {email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send verification email to {email}: {str(e)}")
            return False

    async def send_password_reset_email(
            self,
            email: str,
            username: str,
            token: str
    ) -> bool:
        """Send password reset email."""
        try:
            subject = 'Reset Your Password - Learning Platform'
            reset_url = f"{self.frontend_url}/reset-password?token={token}"
            
            # Create HTML content
            html_content = f"""
            <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px;">
                    <h2 style="color: #e74c3c;">Password Reset Request</h2>
                    <p>Hi <strong>{username}</strong>,</p>
                    <p>You requested a password reset for your Learning Platform account. Click the button below to set a new password:</p>
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{reset_url}" 
                           style="background-color: #e74c3c; color: white; padding: 12px 30px; 
                                  text-decoration: none; border-radius: 5px; display: inline-block;">
                            Reset Password
                        </a>
                    </div>
                    <p>Or copy and paste this link in your browser:</p>
                    <p style="word-break: break-all; color: #7f8c8d;">{reset_url}</p>
                    <p><small>This link will expire in 24 hours.</small></p>
                    <hr style="margin: 30px 0; border: 1px solid #ecf0f1;">
                    <p style="color: #7f8c8d; font-size: 12px;">
                        If you didn't request this reset, please ignore this email. Your password will remain unchanged.
                    </p>
                </div>
            </body>
            </html>
            """
            
            # Plain text version
            plain_content = f"""
            Hi {username},
            
            You requested a password reset for your Learning Platform account.
            Click this link to set a new password:
            
            {reset_url}
            
            This link will expire in 24 hours.
            
            If you didn't request this reset, please ignore this email.
            """

            send_mail(
                subject=subject,
                message=plain_content,
                from_email=self.from_email,
                recipient_list=[email],
                html_message=html_content,
                fail_silently=False
            )
            
            logger.info(f"Password reset email sent to {email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send password reset email to {email}: {str(e)}")
            return False

    async def send_achievement_email(
            self,
            email: str,
            achievement_name: str,
            points: int
    ) -> bool:
        """Send achievement notification email."""
        try:
            subject = f'🎉 Achievement Unlocked: {achievement_name}'
            
            # Create HTML content
            html_content = f"""
            <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <div style="background-color: #f39c12; padding: 20px; border-radius: 10px; text-align: center;">
                    <h1 style="color: white; margin: 0;">🎉 Achievement Unlocked!</h1>
                </div>
                <div style="background-color: #f8f9fa; padding: 20px; border-radius: 0 0 10px 10px;">
                    <h2 style="color: #2c3e50; text-align: center;">{achievement_name}</h2>
                    <p style="text-align: center; font-size: 18px;">
                        You've earned <strong>{points} points</strong>! 
                    </p>
                    <p>Keep up the great work and continue your learning journey!</p>
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{self.frontend_url}/dashboard" 
                           style="background-color: #27ae60; color: white; padding: 12px 30px; 
                                  text-decoration: none; border-radius: 5px; display: inline-block;">
                            View Your Progress
                        </a>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Plain text version
            plain_content = f"""
            🎉 Achievement Unlocked!
            
            {achievement_name}
            
            You've earned {points} points! Keep up the great work and continue your learning journey!
            
            View your progress at: {self.frontend_url}/dashboard
            """

            send_mail(
                subject=subject,
                message=plain_content,
                from_email=self.from_email,
                recipient_list=[email],
                html_message=html_content,
                fail_silently=True  # Don't fail if achievement email fails
            )
            
            logger.info(f"Achievement email sent to {email}: {achievement_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send achievement email to {email}: {str(e)}")
            return False

    async def send_daily_reminder(
            self,
            email: str,
            stats: Dict[str, Any]
    ) -> bool:
        """Send daily study reminder."""
        try:
            subject = '📚 Your Daily Learning Reminder'
            
            username = stats.get('username', 'Learner')
            current_streak = stats.get('current_streak', 0)
            questions_answered_today = stats.get('questions_answered_today', 0)
            daily_goal = stats.get('daily_goal', 20)
            
            # Create HTML content
            html_content = f"""
            <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <div style="background-color: #3498db; padding: 20px; border-radius: 10px 10px 0 0;">
                    <h2 style="color: white; margin: 0;">📚 Daily Learning Reminder</h2>
                </div>
                <div style="background-color: #f8f9fa; padding: 20px; border-radius: 0 0 10px 10px;">
                    <p>Hi <strong>{username}</strong>,</p>
                    <p>It's time for your daily learning session!</p>
                    
                    <div style="background-color: white; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <h3 style="color: #2c3e50; margin-top: 0;">Today's Progress:</h3>
                        <p>🔥 Current streak: <strong>{current_streak} days</strong></p>
                        <p>✅ Questions answered today: <strong>{questions_answered_today}/{daily_goal}</strong></p>
                        {"<p>🎯 You're on track! Keep it up!</p>" if questions_answered_today >= daily_goal else "<p>💪 Time to reach your daily goal!</p>"}
                    </div>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{self.frontend_url}/learn" 
                           style="background-color: #27ae60; color: white; padding: 12px 30px; 
                                  text-decoration: none; border-radius: 5px; display: inline-block;">
                            Start Learning
                        </a>
                    </div>
                    
                    <p><small>You can adjust your reminder preferences in your account settings.</small></p>
                </div>
            </body>
            </html>
            """
            
            # Plain text version
            plain_content = f"""
            Hi {username},
            
            It's time for your daily learning session!
            
            Today's Progress:
            🔥 Current streak: {current_streak} days
            ✅ Questions answered: {questions_answered_today}/{daily_goal}
            
            {"You're on track! Keep it up!" if questions_answered_today >= daily_goal else "Time to reach your daily goal!"}
            
            Start learning: {self.frontend_url}/learn
            
            You can adjust your reminder preferences in your account settings.
            """

            send_mail(
                subject=subject,
                message=plain_content,
                from_email=self.from_email,
                recipient_list=[email],
                html_message=html_content,
                fail_silently=True  # Don't fail if reminder email fails
            )
            
            logger.info(f"Daily reminder sent to {email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send daily reminder to {email}: {str(e)}")
            return False