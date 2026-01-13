"""Email service for sending transactional emails."""
import logging
from typing import Optional

import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class EmailService:
    """
    Service for sending transactional emails.
    
    Uses SMTP for email delivery with proper error handling and logging.
    """

    def __init__(self):
        """Initialize email service with SMTP configuration."""
        self.smtp_host = settings.smtp_host
        self.smtp_port = settings.smtp_port
        self.smtp_user = settings.smtp_user
        self.smtp_password = settings.smtp_password
        self.from_email = settings.smtp_from_email
        self.from_name = settings.smtp_from_name

    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
    ) -> bool:
        """
        Send an email via SMTP.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML email body
            text_content: Plain text email body (fallback)
            
        Returns:
            bool: True if email sent successfully
            
        Raises:
            Exception: If email sending fails after retries
        """
        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = f"{self.from_name} <{self.from_email}>"
            message["To"] = to_email

            # Add text part if provided
            if text_content:
                text_part = MIMEText(text_content, "plain")
                message.attach(text_part)

            # Add HTML part
            html_part = MIMEText(html_content, "html")
            message.attach(html_part)

            # Send email
            await aiosmtplib.send(
                message,
                hostname=self.smtp_host,
                port=self.smtp_port,
                username=self.smtp_user,
                password=self.smtp_password,
                start_tls=True,
            )

            logger.info(f"Email sent successfully to {to_email}: {subject}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}", exc_info=True)
            raise

    async def send_verification_email(
        self, to_email: str, token: str, user_name: str
    ) -> bool:
        """
        Send email verification email.
        
        Args:
            to_email: Recipient email address
            token: Verification token
            user_name: User's name
            
        Returns:
            bool: True if email sent successfully
        """
        # In production, use proper base URL from config
        verification_url = f"http://localhost:3000/verify-email?token={token}"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Verify Your Email</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2563eb;">Verify Your Email Address</h2>
                <p>Hello {user_name},</p>
                <p>Thank you for registering! Please verify your email address by clicking the button below:</p>
                <div style="margin: 30px 0;">
                    <a href="{verification_url}" 
                       style="background-color: #2563eb; color: white; padding: 12px 30px; 
                              text-decoration: none; border-radius: 5px; display: inline-block;">
                        Verify Email
                    </a>
                </div>
                <p>Or copy and paste this link into your browser:</p>
                <p style="color: #666; word-break: break-all;">{verification_url}</p>
                <p style="margin-top: 30px; color: #666; font-size: 14px;">
                    This link will expire in 24 hours. If you didn't create an account, 
                    you can safely ignore this email.
                </p>
            </div>
        </body>
        </html>
        """

        text_content = f"""
        Verify Your Email Address
        
        Hello {user_name},
        
        Thank you for registering! Please verify your email address by clicking this link:
        {verification_url}
        
        This link will expire in 24 hours. If you didn't create an account, 
        you can safely ignore this email.
        """

        return await self.send_email(
            to_email=to_email,
            subject="Verify Your Email Address",
            html_content=html_content,
            text_content=text_content,
        )

    async def send_password_reset_email(
        self, to_email: str, token: str, user_name: str
    ) -> bool:
        """
        Send password reset email.
        
        Args:
            to_email: Recipient email address
            token: Reset token
            user_name: User's name
            
        Returns:
            bool: True if email sent successfully
        """
        reset_url = f"http://localhost:3000/reset-password?token={token}"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Reset Your Password</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2563eb;">Reset Your Password</h2>
                <p>Hello {user_name},</p>
                <p>We received a request to reset your password. Click the button below to create a new password:</p>
                <div style="margin: 30px 0;">
                    <a href="{reset_url}" 
                       style="background-color: #2563eb; color: white; padding: 12px 30px; 
                              text-decoration: none; border-radius: 5px; display: inline-block;">
                        Reset Password
                    </a>
                </div>
                <p>Or copy and paste this link into your browser:</p>
                <p style="color: #666; word-break: break-all;">{reset_url}</p>
                <p style="margin-top: 30px; color: #666; font-size: 14px;">
                    This link will expire in 1 hour. If you didn't request a password reset, 
                    please ignore this email and your password will remain unchanged.
                </p>
            </div>
        </body>
        </html>
        """

        text_content = f"""
        Reset Your Password
        
        Hello {user_name},
        
        We received a request to reset your password. Click this link to create a new password:
        {reset_url}
        
        This link will expire in 1 hour. If you didn't request a password reset, 
        please ignore this email and your password will remain unchanged.
        """

        return await self.send_email(
            to_email=to_email,
            subject="Reset Your Password",
            html_content=html_content,
            text_content=text_content,
        )

    async def send_account_lockout_email(
        self, to_email: str, user_name: str, unlock_minutes: int
    ) -> bool:
        """
        Send account lockout notification email.
        
        Args:
            to_email: Recipient email address
            user_name: User's name
            unlock_minutes: Minutes until auto-unlock
            
        Returns:
            bool: True if email sent successfully
        """
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Account Temporarily Locked</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #dc2626;">Account Temporarily Locked</h2>
                <p>Hello {user_name},</p>
                <p>Your account has been temporarily locked due to too many failed login attempts.</p>
                <p><strong>Your account will automatically unlock in {unlock_minutes} minutes.</strong></p>
                <p style="margin-top: 30px; color: #666; font-size: 14px;">
                    If you didn't attempt to log in, please contact support immediately 
                    as your account may be compromised.
                </p>
            </div>
        </body>
        </html>
        """

        text_content = f"""
        Account Temporarily Locked
        
        Hello {user_name},
        
        Your account has been temporarily locked due to too many failed login attempts.
        
        Your account will automatically unlock in {unlock_minutes} minutes.
        
        If you didn't attempt to log in, please contact support immediately 
        as your account may be compromised.
        """

        return await self.send_email(
            to_email=to_email,
            subject="Account Temporarily Locked",
            html_content=html_content,
            text_content=text_content,
        )
