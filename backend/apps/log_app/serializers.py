from rest_framework import serializers
from apps.log_app.models import DailyLog


class DailyLogSerializer(serializers.ModelSerializer):
    """
    Handles both POST and GET /api/daily-log

    POST validates:
    {
        "date": "2024-03-10",
        "pain": 3,
        "mood": "low",
        "flow": "medium",
        "sleep": 6,
        "stress": "high",
        "exercise": "light"
    }

    GET returns same structure inside "logs": []
    """

    class Meta:
        model  = DailyLog
        fields = ['date', 'pain', 'mood', 'flow', 'sleep', 'stress', 'exercise']

    def validate_pain(self, value):
        if value < 1 or value > 10:
            raise serializers.ValidationError("Pain must be between 1 and 10")
        return value

    def validate_sleep(self, value):
        if value < 0 or value > 24:
            raise serializers.ValidationError("Sleep hours must be between 0 and 24")
        return value