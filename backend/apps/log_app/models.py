from django.db import models
from django.conf import settings


class DailyLog(models.Model):
    """
    Stores daily health log for each user.

    Contract expects:
    POST /api/daily-log
    {
        "date": "2024-03-10",
        "pain": 3,
        "mood": "low",
        "flow": "medium",
        "sleep": 6,
        "stress": "high",
        "exercise": "light"
    }
    """

    MOOD_CHOICES     = [('low', 'Low'), ('medium', 'Medium'), ('high', 'High')]
    FLOW_CHOICES     = [('light', 'Light'), ('medium', 'Medium'), ('heavy', 'Heavy')]
    STRESS_CHOICES   = [('low', 'Low'), ('medium', 'Medium'), ('high', 'High')]
    EXERCISE_CHOICES = [('none', 'None'), ('light', 'Light'), ('moderate', 'Moderate'), ('intense', 'Intense')]

    user     = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='daily_logs'
    )

    date     = models.DateField()
    pain     = models.IntegerField()              # 1-10 scale
    mood     = models.CharField(max_length=10, choices=MOOD_CHOICES)
    flow     = models.CharField(max_length=10, choices=FLOW_CHOICES)
    sleep    = models.FloatField()                # hours
    stress   = models.CharField(max_length=10, choices=STRESS_CHOICES)
    exercise = models.CharField(max_length=10, choices=EXERCISE_CHOICES)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']          # latest first
        unique_together = ['user', 'date']  # one log per day per user

    def __str__(self):
        return f"{self.user.email} — {self.date}"