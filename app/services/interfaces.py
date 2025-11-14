"""
Service interfaces for dependency injection and inversion of control.

This module defines abstract interfaces for service implementations,
enabling dependency injection and making the codebase more testable
and maintainable by decoupling concrete implementations from their usage.
"""

from abc import ABC, abstractmethod
from app_boilerplate.schemas.email import SendEmailRequest, SendEmailResponse


class IEmailService(ABC):
    """
    Abstract interface for email service operations.

    This interface defines the contract that all email service
    implementations must follow, ensuring consistency and enabling
    dependency injection for better testability and maintainability.

    The interface follows the Interface Segregation Principle by defining
    only the essential methods required for email operations.
    """

    @abstractmethod
    async def send_email(self, request: SendEmailRequest) -> SendEmailResponse:
        """
        Send an email to the specified recipient.

        This method should implement the complete email sending process,
        including validation, formatting, and delivery through the email provider.

        Args:
            request (SendEmailRequest): Request containing email details
                                      including recipient, subject, and body

        Returns:
            SendEmailResponse: Response containing the result of the email
                             sending operation with success status and message

        Raises:
            Exception: If there's an error during the email sending process

        Note:
            Implementations should handle errors gracefully and provide
            meaningful error messages for debugging purposes.
        """
        pass
