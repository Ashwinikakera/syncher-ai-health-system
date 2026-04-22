from django.db import models
from django.conf import settings


class DailyLog(models.Model):
    """
    Stores daily health log for NON-PERIOD days.

    POST /api/daily-log
    {
        "date": "2024-03-10",
        "sleep": 6,
        "stress": "high",
        "exercise": "light",
        "medication": "yes",
        "medication_details": "painkiller",
        "food": "junk",
        "routine_change": "yes",
        "routine_details": "travel",
        "white_discharge": "medium",
        "hydration": "yes",
        "symptoms": ["cramps", "fatigue"]
    }
    """

    STRESS_CHOICES   = [('low', 'Low'), ('medium', 'Medium'), ('high', 'High')]
    EXERCISE_CHOICES = [('none', 'None'), ('light', 'Light'), ('moderate', 'Moderate'), ('intense', 'Intense')]
    MEDICATION_CHOICES = [('yes', 'Yes'), ('no', 'No')]
    FOOD_CHOICES     = [('healthy', 'Healthy'), ('junk', 'Junk'), ('mixed', 'Mixed')]
    ROUTINE_CHOICES  = [('yes', 'Yes'), ('no', 'No')]
    DISCHARGE_CHOICES = [('none', 'None'), ('light', 'Light'), ('medium', 'Medium'), ('heavy', 'Heavy')]
    HYDRATION_CHOICES = [('yes', 'Yes'), ('no', 'No')]

    user               = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='daily_logs'
    )
    date               = models.DateField()
    sleep              = models.FloatField()
    stress             = models.CharField(max_length=10, choices=STRESS_CHOICES)
    exercise           = models.CharField(max_length=10, choices=EXERCISE_CHOICES)
    medication         = models.CharField(max_length=5, choices=MEDICATION_CHOICES, default='no')
    medication_details = models.TextField(blank=True, null=True)
    food               = models.CharField(max_length=10, choices=FOOD_CHOICES, default='mixed')
    routine_change     = models.CharField(max_length=5, choices=ROUTINE_CHOICES, default='no')
    routine_details    = models.TextField(blank=True, null=True)
    white_discharge    = models.CharField(max_length=10, choices=DISCHARGE_CHOICES, default='none')
    hydration          = models.CharField(max_length=5, choices=HYDRATION_CHOICES, default='yes')
    symptoms           = models.JSONField(default=list)   # ["cramps", "fatigue"]

    created_at         = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering        = ['-date']
        unique_together = ['user', 'date']

    def __str__(self):
        return f"{self.user.email} — DailyLog {self.date}"


class CycleLog(models.Model):
    """
    Stores health log for PERIOD DAYS only.

    POST /api/cycle-log
    {
        "date": "2024-03-02",
        "pain": 4,
        "mood": "low",
        "flow": "heavy",
        "sleep": 5,
        "stress": "high",
        "exercise": "none",
        "medication": "yes",
        "medication_details": "tablet",
        "hydration": "no"
    }
    """

    MOOD_CHOICES       = [('low', 'Low'), ('medium', 'Medium'), ('high', 'High')]
    FLOW_CHOICES       = [('light', 'Light'), ('medium', 'Medium'), ('heavy', 'Heavy')]
    STRESS_CHOICES     = [('none', 'None'),('low', 'Low'), ('medium', 'Medium'), ('high', 'High')]
    EXERCISE_CHOICES   = [('none', 'None'), ('light', 'Light'), ('moderate', 'Moderate'), ('intense', 'Intense')]
    MEDICATION_CHOICES = [('yes', 'Yes'), ('no', 'No')]
    HYDRATION_CHOICES  = [('yes', 'Yes'), ('no', 'No')]

    user               = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cycle_logs'
    )
    date               = models.DateField()
    pain               = models.IntegerField()           # 1-10
    mood               = models.CharField(max_length=10, choices=MOOD_CHOICES)
    flow               = models.CharField(max_length=10, choices=FLOW_CHOICES)
    sleep              = models.FloatField()
    stress             = models.CharField(max_length=10, choices=STRESS_CHOICES)
    exercise           = models.CharField(max_length=10, choices=EXERCISE_CHOICES)
    medication         = models.CharField(max_length=5, choices=MEDICATION_CHOICES, default='no')
    medication_details = models.TextField(blank=True, null=True)
    hydration          = models.CharField(max_length=5, choices=HYDRATION_CHOICES, default='yes')

    created_at         = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering        = ['-date']
        unique_together = ['user', 'date']

    def __str__(self):
        return f"{self.user.email} — CycleLog {self.date}"