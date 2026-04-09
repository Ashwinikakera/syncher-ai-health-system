from rest_framework import serializers
from apps.health_app.models import MyHealth


class MyHealthSerializer(serializers.ModelSerializer):
    """
    Validates POST /api/my-health

    VALUES MUST MATCH EXACTLY — per contract:
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
    """

    class Meta:
        model  = MyHealth
        fields = [
            'q1', 'q2', 'q3', 'q4', 'q5',
            'q6', 'q7', 'q8', 'q9', 'q10',
            'score', 'risk_level'
        ]
        extra_kwargs = {
            'score':      {'read_only': True},  # set by Dev3 ML
            'risk_level': {'read_only': True},  # set by Dev3 ML
        }

    def validate_q1(self, value):
        valid = ['Regular', 'Occasionally missed', 'Persistent/recurrent']
        if value not in valid:
            raise serializers.ValidationError(f"q1 must be one of: {valid}")
        return value

    def validate_q2(self, value):
        valid = ['Light', 'Moderate', 'Heavy']
        if value not in valid:
            raise serializers.ValidationError(f"q2 must be one of: {valid}")
        return value

    def validate_q3(self, value):
        valid = ['None', 'Noticeable', 'Significant']
        if value not in valid:
            raise serializers.ValidationError(f"q3 must be one of: {valid}")
        return value

    def validate_q4(self, value):
        valid = ['None', 'Mild (1-4 kg)', 'Moderate (5-8 kg)', 'Severe (9+ kg)']
        if value not in valid:
            raise serializers.ValidationError(f"q4 must be one of: {valid}")
        return value

    def validate_q5(self, value):
        valid = ['No', 'Mild', 'Moderate']
        if value not in valid:
            raise serializers.ValidationError(f"q5 must be one of: {valid}")
        return value

    def validate_q6(self, value):
        valid = ['Yes', 'No']
        if value not in valid:
            raise serializers.ValidationError(f"q6 must be one of: {valid}")
        return value

    def validate_q7(self, value):
        valid = ['None', 'Mild', 'Significant']
        if value not in valid:
            raise serializers.ValidationError(f"q7 must be one of: {valid}")
        return value

    def validate_q8(self, value):
        valid = ['Normal energy', 'Mild fatigue', 'Strong fatigue/crashes']
        if value not in valid:
            raise serializers.ValidationError(f"q8 must be one of: {valid}")
        return value

    def validate_q9(self, value):
        valid = ['Never', '1 time/week', '2-3 times/week', 'Daily']
        if value not in valid:
            raise serializers.ValidationError(f"q9 must be one of: {valid}")
        return value

    def validate_q10(self, value):
        valid = ['Healthy', 'Mixed', 'Junk']
        if value not in valid:
            raise serializers.ValidationError(f"q10 must be one of: {valid}")
        return value