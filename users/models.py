from django.db import models
from django.contrib.auth.models import AbstractUser
from uuid6 import uuid7

# Create your models here.
ROLE_CHOICES = [
    ("admin", "admin"),
    ("analyst", "analyst")
]

class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid7, editable=False)
    github_id = models.CharField(max_length=100, unique=True, null=True, blank=True)

    role = models.CharField(choices=ROLE_CHOICES, default="analyst")

    avatar_url = models.URLField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    last_login_at = models.DateTimeField(null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    
class RefreshToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.TextField()
    is_blacklisted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)