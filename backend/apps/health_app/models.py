from django.db import models
from django.conf import settings


class MyHealth(models.Model):
    """
    Stores health questionnaire responses.
    Used for PCOS/metabolic risk scoring by Dev3 ML.
    """

    RISK_CHOICES = [
        ('Low',      'Low'),
        ('Moderate', 'Moderate'),
        ('High',     'High'),
    ]

    user       = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='my_health'
    )

    # Store as plain text — no choices restriction
    # Dev3 ML handles the scoring logic
    q1         = models.CharField(max_length=100)
    q2         = models.CharField(max_length=100)
    q3         = models.CharField(max_length=100)
    q4         = models.CharField(max_length=100)
    q5         = models.CharField(max_length=100)
    q6         = models.CharField(max_length=100)
    q7         = models.CharField(max_length=100)
    q8         = models.CharField(max_length=100)
    q9         = models.CharField(max_length=100)
    q10        = models.CharField(max_length=100)

    # Computed by Dev3 ML
    score      = models.IntegerField(null=True, blank=True)
    risk_level = models.CharField(max_length=10, choices=RISK_CHOICES, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"MyHealth of {self.user.email} — risk: {self.risk_level}"