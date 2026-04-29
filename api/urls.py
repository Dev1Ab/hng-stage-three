from django.urls import path
from .views import ExportProfilesView, PersonPredictionView, PersonPredictionDetailView, ProfileSearchView

urlpatterns = [
    path("profiles/export", ExportProfilesView.as_view(), name="profiles-export"),
    path("profiles/export/", ExportProfilesView.as_view(), name="profiles-export-slash"),

    path("profiles/search", ProfileSearchView.as_view(), name="profile-search"),
    path("profiles/search/", ProfileSearchView.as_view(), name="profile-search-slash"),

    path("profiles/<uuid:id>", PersonPredictionDetailView.as_view(), name="person-detail"),
    path("profiles/<uuid:id>/", PersonPredictionDetailView.as_view(), name="person-detail-slash"),

    path("profiles", PersonPredictionView.as_view(), name="profiles"),
    path("profiles/", PersonPredictionView.as_view(), name="profiles-slash"),
]