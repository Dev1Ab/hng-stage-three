from config.utils import AuthRateThrottle

from .models import User
from rest_framework import generics, viewsets
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAuthenticatedOrReadOnly
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework import status
import hashlib, base64, secrets, requests
from django.conf import settings
from django.shortcuts import get_object_or_404, redirect
from decouple import config
from rest_framework.permissions import IsAdminUser

# Create your views here.

class GitHubLoginView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [AuthRateThrottle]

    def get(self, request):
        code_verifier = secrets.token_urlsafe(64)
        request.session['code_verifier'] = code_verifier
        
        # Create S256 Challenge
        code_challenge = base64.urlsafe_b64encode(
            hashlib.sha256(code_verifier.encode('ascii')).digest()
        ).decode('ascii').replace('=', '')

        github_url = (
            f"https://github.com/login/oauth/authorize"
            f"?client_id={config('GITHUB_CLIENT_ID')}"
            f"&redirect_uri={config('GITHUB_REDIRECT_URI')}"
            f"&scope=read:user user:email"
            f"&code_challenge={code_challenge}"
            f"&code_challenge_method=S256"
        )
        return redirect(github_url)

class GitHubCallbackView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [AuthRateThrottle]

    def get(self, request):
        code = request.GET.get('code')
        code_verifier = request.session.get('code_verifier')

        token_res = requests.post(
            "https://github.com/login/oauth/access_token",
            data={
                "client_id": config('GITHUB_CLIENT_ID'),
                "client_secret": config('GITHUB_CLIENT_SECRET'),
                "code": code,
                "code_verifier": code_verifier, # PKCE Verification
                "redirect_uri": config('GITHUB_REDIRECT_URI'),
            },
            headers={"Accept": "application/json"}
        ).json()

        access_token = token_res.get("access_token")

        # Get User Info from GitHub
        user_res = requests.get(
            "https://api.github.com/user",
            headers={"Authorization": f"token {access_token}"}
        ).json()

        email = user_res.get("email")
        if not email:
            emails_res = requests.get(
                "https://api.github.com/user/emails",
                headers={"Authorization": f"token {access_token}"}
            ).json()

            primary_email = next(
                (e["email"] for e in emails_res if e["primary"] and e["verified"]),
                None
            )

            email = primary_email

        if not email:
            email = f"{user_res['login']}@github.local"

        user, created = User.objects.get_or_create(
            username=user_res['login'],
            defaults={'email': email}
        )

        # Issue JWT Tokens
        refresh = RefreshToken.for_user(user)
        return Response({
            'status': 'success',
            'access_token': str(refresh.access_token),
            'refresh_token': str(refresh),
            'user': user_res['login']
        })

class TokenRefreshView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [AuthRateThrottle]

    def post(self, request):
        refresh_token = request.data.get("refresh_token")

        if not refresh_token:
            return Response({
                    "status":"error", 
                    "message": "Refresh token required"
                }, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            refresh = RefreshToken(refresh_token)

            data = {
                "status": "success",
                "access_token": str(refresh.access_token),
            }

            if config('ROTATE_REFRESH_TOKENS', default=False, cast=bool):
                
                user_id = refresh.payload.get('user_id')

                try:
                    user = User.objects.get(id=user_id)
                except User.DoesNotExist:
                    return Response({
                        "status": "error",
                        "message": "user not found"
                    }, status=status.HTTP_401_UNAUTHORIZED)

                new_refresh = RefreshToken.for_user(user)

                data["refresh_token"] = str(new_refresh)

                try:
                    refresh.blacklist()
                except AttributeError:
                    pass

            return Response(data, status=status.HTTP_200_OK)

        except TokenError:
            return Response(
                {   
                    "status": "error",
                    "message": "Invalid or expired refresh token"},
                status=status.HTTP_400_BAD_REQUEST
            )

class LogoutView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [AuthRateThrottle]

    def post(self, request):
        refresh_token = request.data.get("refresh_token")

        if not refresh_token:
            return Response(
                {
                    "status": "error",
                    "message": "Refresh token required"
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            token = RefreshToken(refresh_token)

            token.blacklist()

            return Response(
                {"status": "success", "message": "Logged out successfully"},
                status=status.HTTP_205_RESET_CONTENT
            )

        except TokenError:
            return Response(
                {"status": "error", "message": "Invalid or expired token"},
                status=status.HTTP_400_BAD_REQUEST
            )

class CreateAdminView(APIView):
    # permission_classes = [IsAdminUser]
    throttle_classes = [AuthRateThrottle]

    def post(self, request, user_id):
        user = get_object_or_404(User, id=user_id)

        user.is_staff = True
        user.role = 'admin'
        user.save()

        return Response({
            "status": "success",
            "message": "User promoted to admin"
        }, status=status.HTTP_200_OK)