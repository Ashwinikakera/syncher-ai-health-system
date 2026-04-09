from django.db import models
from django.conf import settings


class MyHealth(models.Model):
    """
    Stores health questionnaire responses.
    Used for PCOS/metabolic risk scoring by Dev3 ML.

    POST /api/my-health
    {
        "q1": "Persistent/recurrent",
        "q2": "Moderate",
        "q3": "Noticeable",
        "q4": "Moderate (5-8 kg)",
        "q5": "No",
        "q6": "Yes",
        "q7": "Mild",
        "q8": "Strong fatigue/crashes",
        "q9": "2-3 times/week",
        "q10": "Mixed"
    }

    GET /api/my-health returns above + score + risk_level + insights
    """

    # Q1 — Period irregularity
    Q1_CHOICES = [
        ('Regular',              'Regular'),
        ('Occasionally missed',  'Occasionally missed'),
        ('Persistent/recurrent', 'Persistent/recurrent'),
    ]

    # Q2 — Flow intensity
    Q2_CHOICES = [
        ('Light',    'Light'),
        ('Moderate', 'Moderate'),
        ('Heavy',    'Heavy'),
    ]

    # Q3 — Weight changes
    Q3_CHOICES = [
        ('None',       'None'),
        ('Noticeable', 'Noticeable'),
        ('Significant','Significant'),
    ]

    # Q4 — Weight gain amount
    Q4_CHOICES = [
        ('None',              'None'),
        ('Mild (1-4 kg)',     'Mild (1-4 kg)'),
        ('Moderate (5-8 kg)', 'Moderate (5-8 kg)'),
        ('Severe (9+ kg)',    'Severe (9+ kg)'),
    ]

    # Q5 — Facial/body hair
    Q5_CHOICES = [
        ('No',       'No'),
        ('Mild',     'Mild'),
        ('Moderate', 'Moderate'),
    ]

    # Q6 — Acne/skin issues
    Q6_CHOICES = [
        ('Yes', 'Yes'),
        ('No',  'No'),
    ]

    # Q7 — Hair thinning
    Q7_CHOICES = [
        ('None', 'None'),
        ('Mild', 'Mild'),
        ('Significant', 'Significant'),
    ]

    # Q8 — Energy levels
    Q8_CHOICES = [
        ('Normal energy',          'Normal energy'),
        ('Mild fatigue',           'Mild fatigue'),
        ('Strong fatigue/crashes', 'Strong fatigue/crashes'),
    ]

    # Q9 — Exercise frequency
    Q9_CHOICES = [
        ('Never',          'Never'),
        ('1 time/week',    '1 time/week'),
        ('2-3 times/week', '2-3 times/week'),
        ('Daily',          'Daily'),
    ]

    # Q10 — Diet type
    Q10_CHOICES = [
        ('Healthy', 'Healthy'),
        ('Mixed',   'Mixed'),
        ('Junk',    'Junk'),
    ]

    # Risk levels
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

    q1         = models.CharField(max_length=50, choices=Q1_CHOICES)
    q2         = models.CharField(max_length=50, choices=Q2_CHOICES)
    q3         = models.CharField(max_length=50, choices=Q3_CHOICES)
    q4         = models.CharField(max_length=50, choices=Q4_CHOICES)
    q5         = models.CharField(max_length=50, choices=Q5_CHOICES)
    q6         = models.CharField(max_length=50, choices=Q6_CHOICES)
    q7         = models.CharField(max_length=50, choices=Q7_CHOICES)
    q8         = models.CharField(max_length=50, choices=Q8_CHOICES)
    q9         = models.CharField(max_length=50, choices=Q9_CHOICES)
    q10        = models.CharField(max_length=50, choices=Q10_CHOICES)

    # Computed by Dev3 ML — stored after scoring
    score      = models.IntegerField(null=True, blank=True)
    risk_level = models.CharField(max_length=10, choices=RISK_CHOICES, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"MyHealth of {self.user.email} — risk: {self.risk_level}"