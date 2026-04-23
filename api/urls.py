from django.urls import include, path
from django.urls import path
from .views import PersonPredictionView, PersonPredictionDetailView, ProfileSearchView

urlpatterns = [
    path("profiles", PersonPredictionView.as_view()),
    path("profiles/<uuid:id>", PersonPredictionDetailView.as_view(), name="person-detail"),
    path("profiles/search", ProfileSearchView.as_view(), name="profile-search"),
]

