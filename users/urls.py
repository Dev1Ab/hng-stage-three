from django.urls import path
from .views import GitHubLoginView, GitHubCallbackView, GitHubExchangeView, MeView, TokenRefreshView, LogoutView, CreateAdminView, LoginView

urlpatterns = [
    path('login', LoginView.as_view(), name='github-login'),
    path('github', GitHubLoginView.as_view(), name='github-login'),
    path('github/callback', GitHubCallbackView.as_view(), name='github-callback'),
    path('exchange', GitHubExchangeView.as_view(), name='github-exchange'),
    path('me', MeView.as_view(), name='me'),
    path('refresh', TokenRefreshView.as_view(), name='token-refresh'),
    path('logout', LogoutView.as_view(), name='token-logout'),
    path('make-admin/<uuid:user_id>', CreateAdminView.as_view(), name='promote-user'),
]