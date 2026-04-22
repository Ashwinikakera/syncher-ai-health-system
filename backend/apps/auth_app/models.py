from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager


class UserManager(BaseUserManager):
    """
    Custom manager — handles user creation.
    We use email as login instead of username.
    """

    def create_user(self, email, username, password=None):
        if not email:
            raise ValueError("Email is required")
        if not username:
            raise ValueError("Username is required")

        email = self.normalize_email(email)
        user  = self.model(email=email, username=username)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password=None):
        user          = self.create_user(email, username, password)
        user.is_admin = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser):
    # Custom User model.

    username     = models.CharField(max_length=150, unique=True)
    email        = models.EmailField(unique=True)
    is_onboarded = models.BooleanField(default=False)
    is_active    = models.BooleanField(default=True)
    is_admin     = models.BooleanField(default=False)
    created_at   = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD  = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email

    def has_perm(self, perm, obj=None):
        return True

    def has_module_perms(self, app_label):
        return True

    @property
    def is_staff(self):
        return self.is_admin


class Onboarding(models.Model):
    
    # Stores onboarding data — created once per user.
    MOOD_CHOICES = [
        ('low',    'Low'),
        ('medium', 'Medium'),
        ('high',   'High'),
    ]
    FLOW_CHOICES = [
        ('light',  'Light'),
        ('medium', 'Medium'),
        ('heavy',  'Heavy'),
    ]

    user              = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='onboarding'
    )
    age               = models.IntegerField()
    weight            = models.FloatField()
    avg_cycle_length  = models.IntegerField(default=28)

    # List of {start_date, end_date} objects
    cycle_history     = models.JSONField(default=list)

    # Initial symptoms
    pain              = models.IntegerField(default=0)
    mood              = models.CharField(max_length=10, choices=MOOD_CHOICES)
    flow              = models.CharField(max_length=10, choices=FLOW_CHOICES)

    # Medical info
    medical_condition = models.CharField(max_length=100, blank=True, null=True)
    medical_notes     = models.TextField(blank=True, null=True)

    created_at        = models.DateTimeField(auto_now_add=True)
    updated_at        = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Onboarding of {self.user.email}"