from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager


class UserManager(BaseUserManager):
    """
    Custom manager — handles user creation.
    We use email as login instead of username.
    """

    def create_user(self, email, password=None):
        if not email:
            raise ValueError("Email is required")

        email = self.normalize_email(email)
        user = self.model(email=email)
        user.set_password(password)   # hashes the password
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None):
        user = self.create_user(email, password)
        user.is_admin = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser):
    """
    Custom User model.
    Fields:
        - email      → login field (unique)
        - is_onboarded → False on register, True after onboarding
        - is_active  → account active or not
        - is_admin   → superuser flag
        - created_at → when account was created
    """

    email        = models.EmailField(unique=True)
    is_onboarded = models.BooleanField(default=False)
    is_active    = models.BooleanField(default=True)
    is_admin     = models.BooleanField(default=False)
    created_at   = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    # Use email instead of username for login
    USERNAME_FIELD  = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email

    # Required for Django admin
    def has_perm(self, perm, obj=None):
        return True

    def has_module_perms(self, app_label):
        return True

    @property
    def is_staff(self):
        return self.is_admin