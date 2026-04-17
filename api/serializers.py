from .models import Person
from rest_framework import serializers


class PersonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Person
        fields = ["id", "name", "gender", "gender_probability", "sample_size", "age", "age_group", "country_id", "country_probability", "created_at"]
        read_only_fields = ["id", "created_at"]
        
