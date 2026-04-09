from django.db import models
from django.conf import settings


class CycleHistory(models.Model):
    """
    Stores each period cycle logged by the user.

    POST /api/cycle/start → { "start_date": "2024-03-01" }
    POST /api/cycle/end   → { "end_date": "2024-03-05" }

    GET /api/cycle returns:
    {
        "cycles": [
            {
                "start_date": "2024-03-01",
                "end_date": "2024-03-05",
                "cycle_length": 28
            }
        ]
    }
    """

    user         = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cycles'
    )
    start_date   = models.DateField()
    end_date     = models.DateField(null=True, blank=True)  # set later via /end
    cycle_length = models.IntegerField(null=True, blank=True)  # auto calculated
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-start_date']

    def calculate_cycle_length(self):
        """
        Auto calculate cycle length from previous cycle start date.
        """
        previous = CycleHistory.objects.filter(
            user=self.user
        ).exclude(id=self.id).order_by('-start_date').first()

        if previous and previous.start_date:
            delta = self.start_date - previous.start_date
            return delta.days
        else:
            try:
                return self.user.onboarding.avg_cycle_length
            except Exception:
                return 28

    def __str__(self):
        return f"{self.user.email} — {self.start_date} to {self.end_date}"


class PredictionFeedback(models.Model):
    """
    Stores user feedback on ML predictions.

    POST /api/prediction-feedback
    {
        "prediction_correct": false,
        "actual_date": "2024-03-30"
    }
    """

    user               = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='feedbacks'
    )
    prediction_correct = models.BooleanField()
    actual_date        = models.DateField()
    created_at         = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} — correct: {self.prediction_correct}"