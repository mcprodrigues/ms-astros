"""
Email service implementation.

This module implements the business logic for email operations,
orchestrating the use of the EmailClientProvider to send emails
to users with proper validation and error handling.
"""

import uuid
from typing import Annotated
from fastapi import Depends
from .interfaces import IEmailService
from app_boilerplate.providers.email_client import (
    EmailClientProvider,
    get_email_client_provider,
)
from app_boilerplate.schemas.email import SendEmailRequest, SendEmailResponse


class EmailService(IEmailService):
    """
    Service for email operations in the application.

    This service orchestrates the email sending process by coordinating
    the EmailClientProvider to send emails with proper validation,
    formatting, and error handling.

    Attributes:
        email_client (EmailClientProvider): Provider for email sending operations
    """

    def __init__(self, email_client: EmailClientProvider):
        """
        Initialize the email service.

        Args:
            email_client (EmailClientProvider): Configured provider
                                              for email operations
        """
        self.email_client = email_client

    async def send_email(self, request: SendEmailRequest) -> SendEmailResponse:
        """
        Send an email to the specified recipient.

        This method orchestrates the complete email sending process:
        1. Validates the email request data
        2. Delegates to the EmailClientProvider for sending
        3. Returns the result with appropriate status and message

        Args:
            request (SendEmailRequest): Request containing email details

        Returns:
            SendEmailResponse: Response containing the result of the email
                             sending operation

        Raises:
            Exception: If there's an error during the email sending process

        Example:
            >>> service = EmailService(email_client)
            >>> request = SendEmailRequest(
            ...     to_email="user@example.com",
            ...     subject="Welcome",
            ...     body="Welcome to our service!"
            ... )
            >>> response = await service.send_email(request)
            >>> print(response.success)  # True
        """
        try:
            # Generate a unique message ID for tracking
            message_id = f"msg_{uuid.uuid4().hex[:12]}"

            # Send email using the provider
            success = self.email_client.send_email(
                to_email=request.to_email,
                subject=request.subject,
                body=request.body,
                from_email=request.from_email,
                cc_emails=request.cc_emails,
                bcc_emails=request.bcc_emails,
                is_html=request.is_html,
            )

            if success:
                return SendEmailResponse(
                    success=True,
                    message="Email sent successfully",
                    message_id=message_id,
                )
            else:
                return SendEmailResponse(
                    success=False, message="Failed to send email", message_id=message_id
                )

        except Exception as e:
            # Generate message ID even for failed attempts
            message_id = f"msg_{uuid.uuid4().hex[:12]}"

            return SendEmailResponse(
                success=False,
                message=f"Failed to send email: {str(e)}",
                message_id=message_id,
            )


def get_email_service(
    email_client: Annotated[EmailClientProvider, Depends(get_email_client_provider)],
) -> IEmailService:
    """
    Factory function to get the email service.

    Args:
        email_client (EmailClientProvider): Configured provider
                                          for email operations

    Returns:
        IEmailService: Email service instance
    """
    return EmailService(email_client)
