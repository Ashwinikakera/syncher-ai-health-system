from rest_framework import serializers
from apps.user_app.models import UserProfile


class OnboardingSerializer(serializers.ModelSerializer):
    """
    Validates POST /api/onboarding
    Contract expects:
    {
        "age": 22,
        "weight": 55,
        "cycle_history": ["2024-01-01", "2024-01-28", "2024-02-25"],
        "avg_cycle_length": 28
    }
    """

    cycle_history = serializers.ListField(
        child=serializers.DateField(input_formats=['%Y-%m-%d']),
        min_length=1
    )

    class Meta:
        model  = UserProfile
        fields = ['age', 'weight', 'cycle_history', 'avg_cycle_length']

    def validate_age(self, value):
        if value < 10 or value > 60:
            raise serializers.ValidationError("Please enter a valid age")
        return value

    def validate_weight(self, value):
        if value < 20 or value > 300:
            raise serializers.ValidationError("Please enter a valid weight")
        return value

    def validate_avg_cycle_length(self, value):
        if value < 15 or value > 45:
            raise serializers.ValidationError("Cycle length must be between 15 and 45 days")
        return value

    def validate_cycle_history(self, value):
        # Convert date objects back to strings for JSONField storage
        return [str(d) for d in value]