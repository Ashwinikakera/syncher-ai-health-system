from django.db import models
from django.conf import settings


class CycleHistory(models.Model):
    """
    Stores each period cycle logged by the user.

    Contract expects:
    POST /api/cycle
    {
        "start_date": "2024-03-01",
        "end_date": "2024-03-05"
    }

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
    end_date     = models.DateField()
    cycle_length = models.IntegerField(null=True, blank=True)  # auto calculated
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-start_date']  # latest first

    def save(self, *args, **kwargs):
        # Auto calculate cycle length from previous cycle
        previous = CycleHistory.objects.filter(
            user=self.user
        ).order_by('-start_date').first()

        if previous and previous.start_date:
            delta = self.start_date - previous.start_date
            self.cycle_length = delta.days
        else:
            # First cycle — use user's avg_cycle_length from profile
            try:
                self.cycle_length = self.user.profile.avg_cycle_length
            except Exception:
                self.cycle_length = 28  # default

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.email} — {self.start_date} to {self.end_date}"