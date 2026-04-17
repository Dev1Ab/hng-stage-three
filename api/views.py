from rest_framework.generics import CreateAPIView, RetrieveDestroyAPIView, ListAPIView, ListCreateAPIView
from rest_framework.response import Response
from rest_framework import status
import requests
from datetime import datetime, timezone
from uuid6 import uuid7
from decouple import config

from .serializers import PersonSerializer
from .models import Person


GENDERIZE_API_URL = config("GENDERIZE_API_URL")
AGIFY_API_URL = config("AGIFY_API_URL")
NATIONALIZE_API_URL = config("NATIONALIZE_API_URL")


class PersonPredictionView(ListCreateAPIView):
    serializer_class = PersonSerializer
    queryset = Person.objects.all()

    def create(self, request, *args, **kwargs):
        name = request.data.get("name")

        if not name or not name.strip():
            return Response({
                "status": "error",
                "message": "Name is required"
            }, status=status.HTTP_400_BAD_REQUEST)

        existing = Person.objects.filter(name__iexact=name).first()
        if existing:
            return Response({
                "status": "success",
                "message": "Profile already exists",
                "data": PersonSerializer(existing).data
            }, status=status.HTTP_200_OK)

        try:
            gender_res = requests.get(GENDERIZE_API_URL, params={"name": name}, timeout=5).json()
            age_res = requests.get(AGIFY_API_URL, params={"name": name}, timeout=5).json()
            country_res = requests.get(NATIONALIZE_API_URL, params={"name": name}, timeout=5).json()

            if (gender_res.get("gender") is None or gender_res.get("count", 0) == 0):
                return Response(
                    {"status": "error", "message": "Genderize returned an invalid response"},
                    status=status.HTTP_502_BAD_GATEWAY
                )

            if age_res.get("age") is None:
                return Response(
                    {"status": "error", "message": "Agify returned an invalid response"},
                    status=status.HTTP_502_BAD_GATEWAY
                )
            
            countries = country_res.get("country", [])
            if not countries:
                return Response(
                    {"status": "error", "message": "Nationalize returned an invalid response"},
                    status=status.HTTP_502_BAD_GATEWAY
                )

            top_country = max(countries, key=lambda x: x.get("probability", 0))

            data = {
                "name": name,

                "gender": gender_res.get("gender"),
                "gender_probability": gender_res.get("probability"),
                "sample_size": gender_res.get("count"),

                "age": age_res.get("age"),
                "age_group": self.get_age_group(age_res.get("age")),

                "country_id": top_country.get("country_id"),
                "country_probability": top_country.get("probability"),

            }

            serializer = self.get_serializer(data=data)
            serializer.is_valid(raise_exception=True)
            serializer.save()

            return Response({
                "status": "success",
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)

        except requests.exceptions.RequestException:
            return Response(
                {"status": "error", "message": "External API request failed"},
                status=status.HTTP_502_BAD_GATEWAY
            )

    def get_age_group(self, age):
        if age is None:
            return None
        if 0 <= age <= 12:
            return "child"
        elif 13 <= age <= 19:
            return "teenager"
        elif 20 <= age <= 59:
            return "adult"
        return "senior"

    def get_queryset(self):
        queryset = Person.objects.all()

        gender = self.request.query_params.get("gender")
        country = self.request.query_params.get("country_id")
        age_group = self.request.query_params.get("age_group")

        if gender:
            queryset = queryset.filter(gender__iexact=gender)

        if country:
            queryset = queryset.filter(country_id__iexact=country)

        if age_group:
            queryset = queryset.filter(age_group__iexact=age_group)

        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)

        simplified_data = [
            {
                "id": item["id"],
                "name": item["name"],
                "gender": item["gender"],
                "age": item["age"],
                "age_group": item["age_group"],
                "country_id": item["country_id"],
            }
            for item in serializer.data
        ]

        return Response({
            "status": "success",
            "count": len(simplified_data),
            "data": simplified_data
        })
    
class PersonPredictionDetailView(RetrieveDestroyAPIView):
    queryset = Person.objects.all()
    serializer_class = PersonSerializer
    lookup_field = "id"

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)

        return Response({
            "status": "success",
            "data": serializer.data
        })
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)