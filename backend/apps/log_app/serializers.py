from rest_framework import serializers
from apps.log_app.models import DailyLog, CycleLog


class DailyLogSerializer(serializers.ModelSerializer):
    """
    Handles POST and GET /api/daily-log

    POST validates:
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

    symptoms = serializers.ListField(
        child   = serializers.CharField(),
        default = list
    )

    class Meta:
        model  = DailyLog
        fields = [
            'date', 'sleep', 'stress', 'exercise',
            'medication', 'medication_details',
            'food', 'routine_change', 'routine_details',
            'white_discharge', 'hydration', 'symptoms'
        ]

    def validate_sleep(self, value):
        if value < 0 or value > 24:
            raise serializers.ValidationError("Sleep hours must be between 0 and 24")
        return value


class CycleLogSerializer(serializers.ModelSerializer):
    """
    Handles POST and GET /api/cycle-log

    POST validates:
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

    class Meta:
        model  = CycleLog
        fields = [
            'date', 'pain', 'mood', 'flow',
            'sleep', 'stress', 'exercise',
            'medication', 'medication_details',
            'hydration'
        ]

    def validate_pain(self, value):
        if value < 1 or value > 10:
            raise serializers.ValidationError("Pain must be between 1 and 10")
        return value

    def validate_sleep(self, value):
        if value < 0 or value > 24:
            raise serializers.ValidationError("Sleep hours must be between 0 and 24")
        return value