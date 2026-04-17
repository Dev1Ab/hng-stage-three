from django.urls import include, path
from django.urls import path
from .views import PersonPredictionView, PersonPredictionDetailView

urlpatterns = [
    path("profiles/", PersonPredictionView.as_view()),
    path("profiles/<uuid:id>/", PersonPredictionDetailView.as_view(), name="person-detail"),
]

