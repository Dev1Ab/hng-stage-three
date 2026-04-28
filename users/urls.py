from django.urls import path
from .views import GitHubLoginView, GitHubCallbackView, TokenRefreshView, LogoutView

urlpatterns = [
    path('github', GitHubLoginView.as_view(), name='github-login'),
    path('github/callback', GitHubCallbackView.as_view(), name='github-callback'),
    path('refresh', TokenRefreshView.as_view(), name='token-refresh'),
    path('logout', LogoutView.as_view(), name='token-logout'),
]