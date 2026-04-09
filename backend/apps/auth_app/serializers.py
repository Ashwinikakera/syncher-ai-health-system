from rest_framework import serializers
from apps.auth_app.models import User, Onboarding


class RegisterSerializer(serializers.ModelSerializer):
<<<<<<< HEAD
=======
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
>>>>>>> d98ae17 (dev 1 editing done)
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model  = User
<<<<<<< HEAD
        fields = ['username', 'email', 'password', 'confirm_password']  # ← added username
=======
        fields = ['username', 'email', 'password', 'confirm_password']
>>>>>>> d98ae17 (dev 1 editing done)
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

<<<<<<< HEAD
    def validate_username(self, value):                              # ← add this
=======
    def validate_username(self, value):
>>>>>>> d98ae17 (dev 1 editing done)
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username already taken")
        return value

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        user = User.objects.create_user(
            username = validated_data['username'],                   # ← added
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
    Validates POST /api/onboarding
    Contract expects:
    {
        "age": 22,
        "weight": 55,
        "cycle_history": [
            {"start_date": "2024-01-01", "end_date": "2024-01-05"},
            {"start_date": "2024-01-28", "end_date": "2024-02-01"}
        ],
        "avg_cycle_length": 28,
        "pain": 3,
        "mood": "low",
        "flow": "medium",
        "medical_condition": "PCOS",
        "medical_notes": "missed periods in last 6 months"
    }
    """

    cycle_history = serializers.ListField(
        child     = serializers.DictField(child=serializers.CharField()),
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
        if value < 15 or value > 45:
            raise serializers.ValidationError("Cycle length must be between 15 and 45 days")
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