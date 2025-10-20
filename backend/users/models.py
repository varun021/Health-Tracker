from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MinLengthValidator
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """
    Custom User model extending Django's AbstractUser.
    Adds email uniqueness and additional user profile fields.
    """
    
    # Override email to make it required and unique
    email = models.EmailField(
        _('email address'),
        unique=True,
        error_messages={
            'unique': _("A user with that email already exists."),
        }
    )
    
    # Profile fields
    bio = models.TextField(
        _('biography'),
        max_length=500,
        blank=True,
        help_text=_('Brief description about the user')
    )
    
    profile_image = models.ImageField(
        _('profile image'),
        upload_to='profile_images/',
        blank=True,
        null=True
    )
    
    # Verification and account status
    is_verified = models.BooleanField(
        _('verified'),
        default=False,
        help_text=_('Designates whether the user has verified their email.')
    )
    
    # Timestamps
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    # Optional: Additional fields
    phone_number = models.CharField(
        _('phone number'),
        max_length=15,
        blank=True,
        validators=[MinLengthValidator(10)]
    )
    
    date_of_birth = models.DateField(
        _('date of birth'),
        blank=True,
        null=True
    )
    
    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['username']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return self.username
    
    @property
    def full_name(self):
        """Returns the user's full name."""
        return f"{self.first_name} {self.last_name}".strip() or self.username
    
    @property
    def is_profile_complete(self):
        """Check if user has completed their profile."""
        return all([
            self.first_name,
            self.last_name,
            self.email,
            self.bio,
        ])
    
    def get_short_name(self):
        """Return the short name for the user."""
        return self.first_name or self.username