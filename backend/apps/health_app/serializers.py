from rest_framework import serializers
from apps.health_app.models import MyHealth


class MyHealthSerializer(serializers.ModelSerializer):
    """
    Handles POST and GET /api/my-health
    Accepts any string values for q1-q10.
    Dev3 ML handles scoring logic.
    """

    class Meta:
        model  = MyHealth
        fields = [
            'q1', 'q2', 'q3', 'q4', 'q5',
            'q6', 'q7', 'q8', 'q9', 'q10',
            'score', 'risk_level'
        ]
        extra_kwargs = {
            'score':      {'read_only': True},
            'risk_level': {'read_only': True},
        }

    def validate(self, data):
        # Just check all 10 questions are present
        for i in range(1, 11):
            key = f'q{i}'
            if not data.get(key):
                raise serializers.ValidationError(f"{key} is required")
        return data