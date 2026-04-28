import re
from .permissions import IsAdmin
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import CreateAPIView, RetrieveDestroyAPIView, ListAPIView, ListCreateAPIView, ValidationError
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import requests
from datetime import datetime, timezone
from uuid6 import uuid7
from decouple import config
from rest_framework.pagination import PageNumberPagination

from .serializers import PersonSerializer
from .models import Person


GENDERIZE_API_URL = config("GENDERIZE_API_URL")
AGIFY_API_URL = config("AGIFY_API_URL")
NATIONALIZE_API_URL = config("NATIONALIZE_API_URL")

class Pagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'limit'
    max_page_size = 50

    def get_paginated_response(self, data):
        return Response({
            "status": "success",
            "page": self.page.number,
            "limit": self.get_page_size(self.request),
            "total": self.page.paginator.count,
            "total_pages": self.page.paginator.num_pages,
            "links": {
                "next": self.get_next_link(),
                "previous": self.get_previous_link()
            },
            "data": data
        })

class PersonPredictionView(ListCreateAPIView):
    serializer_class = PersonSerializer
    queryset = Person.objects.all()
    pagination_class = Pagination

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAdmin(), IsAuthenticated()]
        return [IsAuthenticated()]

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

        params = self.request.query_params

        min_age = params.get("min_age")
        max_age = params.get("max_age")
        min_gender_probability = params.get("min_gender_probability")
        min_country_probability = params.get("min_country_probability")

        if params.get("gender"):
            queryset = queryset.filter(gender__iexact=params.get("gender").lower())

        if params.get("age_group"):
            queryset = queryset.filter(age_group__iexact=params.get("age_group"))

        if params.get("country_id"):
            queryset = queryset.filter(country_id__iexact=params.get("country_id"))

        if min_age:
            queryset = queryset.filter(age__gte=int(min_age))

        if max_age:
            queryset = queryset.filter(age__lte=int(max_age))

        if min_gender_probability:
            queryset = queryset.filter(gender_probability__gte=float(min_gender_probability))

        if min_country_probability:
            queryset = queryset.filter(country_probability__gte=float(min_country_probability))

        sort_by = params.get("sort_by", "created_at")
        order = params.get("order", "asc")

        if order not in ["asc", "desc"]:
            raise ValidationError("Invalid query parameters")

        allowed_sort = ["age", "created_at", "gender_probability"]

        if sort_by not in allowed_sort:
            raise ValidationError("Invalid query parameters")

        if sort_by in allowed_sort:
            if order == "desc":
                sort_by = f"-{sort_by}"
            queryset = queryset.order_by(sort_by)

        return queryset

    def list(self, request, *args, **kwargs):
        params = request.query_params

        try:
            min_age = params.get("min_age")
            if min_age and not min_age.isdigit():
                raise ValueError

            max_age = params.get("max_age")
            if max_age and not max_age.isdigit():
                raise ValueError

            if params.get("min_gender_probability"):
                gp = float(params.get("min_gender_probability"))
                if not (0 <= gp <= 1):
                    raise ValueError

            if params.get("min_country_probability"):
                cp = float(params.get("min_country_probability"))
                if not (0 <= cp <= 1):
                    raise ValueError

        except:
            return Response({
                "status": "error",
                "message": "Invalid query parameters"
            }, status=422)

        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
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
    
class ProfileSearchView(ListAPIView):
    serializer_class = PersonSerializer
    pagination_class = Pagination

    def get_queryset(self):
        q = self.request.query_params.get("q", "").lower()

        if not q or not q.strip():
            self.invalid_query = True
            return Person.objects.none()

        self.interpreted = False
        qs = Person.objects.all()

        has_male = re.search(r"\bmales?\b", q)
        has_female = re.search(r"\bfemales?\b", q)
        if has_male and has_female:
            self.interpreted = True
        elif has_male:
            qs = qs.filter(gender="male")
            self.interpreted = True
        elif has_female:
            qs = qs.filter(gender="female")
            self.interpreted = True

        age_groups = ["teenager", "adult", "child", "senior"]
        for group in age_groups:
            if group in q or (group == "teenager" and "teen" in q):
                qs = qs.filter(age_group=group)
                self.interpreted = True

        if "young" in q:
            qs = qs.filter(age__gte=16, age__lte=24)
            self.interpreted = True

        above_match = re.search(r"above (\d+)", q)
        if above_match:
            qs = qs.filter(age__gte=int(above_match.group(1))) # Or >= based on specific test needs
            self.interpreted = True

        countries = Person.objects.values_list("country_name", "country_id")
        for name, code in countries:
            if re.search(rf"\b{name.lower()}\b", q):
                qs = qs.filter(country_id=code)
                self.interpreted = True

        return qs

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        if not getattr(self, "interpreted", False):
            return Response({
                "status": "error",
                "message": "Unable to interpret query"
            }, status=400)
        
        if getattr(self, "invalid_query", False):
            return Response({
                "status": "error",
                "message": "q parameter is required"
            }, status=400)

        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)