from rest_framework import serializers
from apps.auth_app.models import User


class RegisterSerializer(serializers.ModelSerializer):
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model  = User
        fields = ['username', 'email', 'password', 'confirm_password']  # ← added username
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

    def validate_username(self, value):                              # ← add this
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username already taken")
        return value

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        user = User.objects.create_user(
            username = validated_data['username'],                   # ← added
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