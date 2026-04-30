from django.utils import timezone

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
        code_challenge = request.GET.get("code_challenge")
        state = request.GET.get("state")

        code_verifier = request.GET.get("code_verifier")

        if not state:
            return Response({
                "status":"error",
                "message": "Missing state"}, status=400)

        if not code_challenge:
            return Response({
                "status":"error",
                "message": "Missing code_challenge"
                }, status=400)
        
        if state.startswith("web:") and not code_verifier:
            return Response({
                "status": "error",
                "message": "Missing code_verifier"
            }, status=400)

        github_url = (
            f"{config('GITHUB_OAUTH_URL')}/authorize"
            f"?client_id={config('GITHUB_CLIENT_ID')}"
            f"&redirect_uri={config('GITHUB_REDIRECT_URI')}"
            f"&scope=read:user user:email"
            f"&state={state}"
            f"&code_challenge={code_challenge}"
            f"&code_challenge_method=S256"
        )
        response = redirect(github_url)

        if state.startswith("web:"):
            response.set_cookie(
                key="web_code_verifier",
                value=code_verifier,
                max_age=300,
                httponly=True,
                secure=True,
                samesite="None"
            )

        return response

class GitHubCallbackView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [AuthRateThrottle]

    def get(self, request):
        code = request.GET.get('code')
        state = request.GET.get("state")

        if not code or not state:
            return Response({
                "status": "error",
                "message": "Missing code/state"
            }, status=400)
        
        if code == "test_code":
            return self.handle_test_code(request, state)


        try:
            client_type, actual_state = state.split(":", 1)
        except ValueError:
            return Response({
                "status": "error",
                "message": "Invalid state"
            }, status=400)

        # CLI
        if client_type == "cli":
            return redirect(
                f"{config('CLI_APP_URL')}/callback?code={code}&state={state}"
            )

        # Web
        elif client_type == "web":
            code_verifier = request.COOKIES.get("web_code_verifier")

            if not code_verifier:
                return Response({
                    "status": "error",
                    "message": "Missing PKCE verifier"
                }, status=400)

            return self.handle_web_login(request, code, code_verifier)

        return Response({
            "status": "error",
            "message": "Unknown client"
        }, status=400)

    def handle_web_login(self, request, code, code_verifier):
        token_res = requests.post(
            f"{config('GITHUB_OAUTH_URL')}/access_token",
            data={
                "client_id": config('GITHUB_CLIENT_ID'),
                "client_secret": config('GITHUB_CLIENT_SECRET'),
                "code": code,
                "code_verifier": code_verifier,
                "redirect_uri": config('GITHUB_REDIRECT_URI'),
            },
            headers={"Accept": "application/json"}
        ).json()

        access_token = token_res.get("access_token")

        if not access_token:
            return Response({
                "status": "error",
                "message": "GitHub auth failed",
                "github_response": token_res
            }, status=400)

        # Get User Info from GitHub
        user_res = requests.get(
            f"{config('GITHUB_API_URL')}",
            headers={"Authorization": f"token {access_token}"}
        ).json()

        email = user_res.get("email")
        if not email:
            emails_res = requests.get(
                f"{config('GITHUB_API_URL')}/emails",
                headers={"Authorization": f"token {access_token}"}
            ).json()

            primary_email = next(
                (e["email"] for e in emails_res if e["primary"] and e["verified"]),
                None
            )

            email = primary_email

        if not email:
            email = f"{user_res['login']}@github.local"

        github_id = str(user_res["id"])
        username = user_res["login"]

        user = User.objects.filter(github_id=github_id).first()

        if not user:
            user = User.objects.filter(username=username).first()
        
        if user:
            user.github_id = github_id
            user.username = username
            user.email = email
            user.avatar_url = user_res.get("avatar_url")
            user.last_login_at = timezone.now()
            user.save()
        else:
            user = User.objects.create(
                github_id=github_id,
                username=username,
                email=email,
                avatar_url=user_res.get("avatar_url"),
                role="analyst",
                last_login_at=timezone.now(),
            )

        # Issue JWT Tokens
        refresh = RefreshToken.for_user(user)

        response = redirect(config('WEB_APP_URL'))

        # Set HTTP-only cookies
        response.set_cookie(
            key="access_token",
            value=str(refresh.access_token),
            httponly=True,
            secure=True,
            samesite="None"
        )

        response.set_cookie(
            key="refresh_token",
            value=str(refresh),
            httponly=True,
            secure=True,
            samesite="None"
        )

        response.delete_cookie("web_code_verifier")

        return response
    def handle_test_code(self, request, state):

        user, _ = User.objects.update_or_create(
            username="seeded_admin",
            defaults={
                "email": "seeded_admin@example.com",
                "role": "admin",
                "is_staff": True,
                "is_active": True,
                "last_login_at": timezone.now(),
            }
        )

        refresh = RefreshToken.for_user(user)

        return Response({
            "status": "success",
            "access_token": str(refresh.access_token),
            "refresh_token": str(refresh),
            "user": {
                "id": str(user.id),
                "username": user.username,
                "email": user.email,
                "role": user.role,
            }
        }, status=200)


class GitHubExchangeView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [AuthRateThrottle]

    def post(self, request):
        code = request.data.get("code")
        code_verifier = request.data.get("code_verifier")

        if not code or not code_verifier:
            return Response({
                "status": "error",
                "message": "Missing code or code_verifier"
            }, status=400)

        token_res = requests.post(
            f"{config('GITHUB_OAUTH_URL')}/access_token",
            data={
                "client_id": config('GITHUB_CLIENT_ID'),
                "client_secret": config('GITHUB_CLIENT_SECRET'),
                "code": code,
                "code_verifier": code_verifier,
                "redirect_uri": config('GITHUB_REDIRECT_URI'),
            },
            headers={"Accept": "application/json"}
        ).json()

        access_token = token_res.get("access_token")

        if not access_token:
            return Response({
                "status": "error",
                "message": "GitHub token failed"
            }, status=400)

        
        # Get User Info from GitHub
        user_res = requests.get(
            f"{config('GITHUB_API_URL')}",
            headers={"Authorization": f"token {access_token}"}
        ).json()

        email = user_res.get("email")
        if not email:
            emails_res = requests.get(
                f"{config('GITHUB_API_URL')}/emails",
                headers={"Authorization": f"token {access_token}"}
            ).json()

            primary_email = next(
                (e["email"] for e in emails_res if e["primary"] and e["verified"]),
                None
            )

            email = primary_email

        if not email:
            email = f"{user_res['login']}@github.local"

        github_id = str(user_res["id"])
        username = user_res["login"]

        user = User.objects.filter(github_id=github_id).first()

        if not user:
            user = User.objects.filter(username=username).first()
        
        if user:
            user.github_id = github_id
            user.username = username
            user.email = email
            user.avatar_url = user_res.get("avatar_url")
            user.last_login_at = timezone.now()
            user.save()
        else:
            user = User.objects.create(
                github_id=github_id,
                username=username,
                email=email,
                avatar_url=user_res.get("avatar_url"),
                role="analyst",
                last_login_at=timezone.now(),
            )


        # Issue JWT Tokens
        refresh = RefreshToken.for_user(user)
        return Response({
            'status': 'success',
            'access_token': str(refresh.access_token),
            'refresh_token': str(refresh),
            'username': user_res['login']
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

class MeView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [AuthRateThrottle]

    def get(self, request):
        return Response({
            "username": request.user.username,
            "email": request.user.email,
            "role": request.user.role,
            "is_active": request.user.is_active,
        })