from rest_framework import serializers
from apps.auth_app.models import User, Onboarding


class RegisterSerializer(serializers.ModelSerializer):
    """
    Validates POST /api/register
    Contract expects:
    {
        "username": "user1",
        "email": "user@gmail.com",
        "password": "123456",
        "confirm_password": "123456"
    }
    """
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model  = User
        fields = ['username', 'email', 'password', 'confirm_password']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match")
        return data

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already registered")
        return value

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username already taken")
        return value

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        user = User.objects.create_user(
            email    = validated_data['email'],
            username = validated_data['username'],
            password = validated_data['password']
        )
        return user


class LoginSerializer(serializers.Serializer):
    """
    Validates POST /api/login
    {
        "email": "user@gmail.com",
        "password": "123456"
    }
    """
    email    = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class OnboardingSerializer(serializers.ModelSerializer):
    """
    this Validates POST /api/onboarding
    """

    cycle_history = serializers.ListField(
        child      = serializers.DictField(child=serializers.CharField()),
        min_length = 1
    )

    class Meta:
        model  = Onboarding
        fields = [
            'age', 'weight', 'cycle_history', 'avg_cycle_length',
            'pain', 'mood', 'flow',
            'medical_condition', 'medical_notes'
        ]

    def validate_age(self, value):
        if value < 10 or value > 60:
            raise serializers.ValidationError("Please enter a valid age")
        return value

    def validate_weight(self, value):
        if value < 20 or value > 300:
            raise serializers.ValidationError("Please enter a valid weight")
        return value

    def validate_avg_cycle_length(self, value):
        # Relaxed validation — PCOS/irregular users can have longer cycles
        value = abs(value)
        if value < 10 or value > 180:
            raise serializers.ValidationError("Please enter a valid cycle length")
        return value

    def validate_pain(self, value):
        if value < 0 or value > 10:
            raise serializers.ValidationError("Pain must be between 0 and 10")
        return value

    def validate_cycle_history(self, value):
        # Validate each entry has start_date and end_date
        for entry in value:
            if 'start_date' not in entry or 'end_date' not in entry:
                raise serializers.ValidationError(
                    "Each cycle_history entry must have start_date and end_date"
                )
        return value
