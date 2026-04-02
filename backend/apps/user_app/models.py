from django.db import models
from django.conf import settings


class UserProfile(models.Model):
    """
    Stores onboarding data for each user.
    Created once when user completes onboarding.

    Contract expects:
    {
        "age": 22,
        "weight": 55,
        "cycle_history": ["2024-01-01", "2024-01-28", "2024-02-25"],
        "avg_cycle_length": 28
    }
    """

    # Link to our custom User model
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile'
    )

    age              = models.IntegerField()
    weight           = models.FloatField()                        # in kg
    avg_cycle_length = models.IntegerField(default=28)            # in days

    # Stores list of date strings e.g ["2024-01-01", "2024-01-28"]
    cycle_history    = models.JSONField(default=list)

    created_at       = models.DateTimeField(auto_now_add=True)
    updated_at       = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile of {self.user.email}"