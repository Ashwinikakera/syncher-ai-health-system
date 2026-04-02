from rest_framework import serializers
from apps.auth_app.models import User


class RegisterSerializer(serializers.ModelSerializer):
    """
    Validates POST /api/register
    Contract expects:
    {
        "email": "user@gmail.com",
        "password": "123456",
        "confirm_password": "123456"
    }
    """
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model  = User
        fields = ['email', 'password', 'confirm_password']
        extra_kwargs = {
            'password': {'write_only': True}  # never return password in response
        }

    def validate(self, data):
        # Check passwords match
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match")
        return data

    def validate_email(self, value):
        # Check email not already registered
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already registered")
        return value

    def create(self, validated_data):
        # Remove confirm_password before saving
        validated_data.pop('confirm_password')
        user = User.objects.create_user(
            email    = validated_data['email'],
            password = validated_data['password']
        )
        return user


class LoginSerializer(serializers.Serializer):
    """
    Validates POST /api/login
    Contract expects:
    {
        "email": "user@gmail.com",
        "password": "123456"
    }
    """
    email    = serializers.EmailField()
    password = serializers.CharField(write_only=True)