from uuid6 import uuid7
from django.db import models


# Create your models here.
class Person(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid7, editable=False)
    name = models.CharField(max_length=100, unique=True)

    gender = models.CharField(max_length=10)
    gender_probability = models.FloatField()


    age = models.IntegerField()
    age_group = models.CharField(max_length=20)

    country_id = models.CharField(max_length=2)
    country_name = models.CharField(max_length=100)
    country_probability = models.FloatField()

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.country_name})"

    class Meta:
        indexes = [
            models.Index(fields=["gender"]),
            models.Index(fields=["age"]),
            models.Index(fields=["age_group"]),
            models.Index(fields=["country_id"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["gender_probability"]),
            models.Index(fields=["country_probability"]),

            models.Index(fields=["country_id", "gender", "age"]),
            models.Index(fields=["country_id", "age_group"]),
            models.Index(fields=["gender", "age"]),
        ]