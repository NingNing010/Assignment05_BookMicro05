import os
from datetime import datetime, timedelta, timezone

import jwt
from django.contrib.auth.hashers import make_password, check_password
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import UserAccount
from .serializers import RegisterSerializer, UserSerializer

JWT_SECRET = os.getenv('JWT_SECRET', 'bookstore-jwt-secret')
JWT_ALGORITHM = 'HS256'
ACCESS_MINUTES = int(os.getenv('JWT_ACCESS_MINUTES', '60'))
REFRESH_DAYS = int(os.getenv('JWT_REFRESH_DAYS', '7'))


def _build_token(user: UserAccount, token_type: str, ttl: timedelta) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        'sub': str(user.id),
        'email': user.email,
        'role': user.role,
        'type': token_type,
        'iat': int(now.timestamp()),
        'exp': int((now + ttl).timestamp()),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def _extract_bearer(request):
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return None
    return auth_header.split(' ', 1)[1].strip()


def _decode_token(token: str):
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])


class RegisterView(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data['email']
        if UserAccount.objects.filter(email=email).exists():
            return Response({'error': 'Email already exists'}, status=status.HTTP_400_BAD_REQUEST)

        user = UserAccount.objects.create(
            email=email,
            password=make_password(serializer.validated_data['password']),
            full_name=serializer.validated_data.get('full_name', ''),
            role=serializer.validated_data.get('role', 'customer'),
        )
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password', '')
        if not email or not password:
            return Response({'error': 'email and password are required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = UserAccount.objects.get(email=email, is_active=True)
        except UserAccount.DoesNotExist:
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

        if not check_password(password, user.password):
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

        access_token = _build_token(user, 'access', timedelta(minutes=ACCESS_MINUTES))
        refresh_token = _build_token(user, 'refresh', timedelta(days=REFRESH_DAYS))
        return Response({
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': UserSerializer(user).data,
        })


class RefreshView(APIView):
    def post(self, request):
        refresh_token = request.data.get('refresh_token')
        if not refresh_token:
            return Response({'error': 'refresh_token is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            payload = _decode_token(refresh_token)
            if payload.get('type') != 'refresh':
                return Response({'error': 'Invalid token type'}, status=status.HTTP_400_BAD_REQUEST)
            user = UserAccount.objects.get(id=int(payload['sub']), is_active=True)
        except Exception:
            return Response({'error': 'Invalid or expired refresh token'}, status=status.HTTP_401_UNAUTHORIZED)

        access_token = _build_token(user, 'access', timedelta(minutes=ACCESS_MINUTES))
        return Response({'access_token': access_token})


class ValidateView(APIView):
    def post(self, request):
        token = request.data.get('token') or _extract_bearer(request)
        if not token:
            return Response({'valid': False, 'error': 'missing token'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            payload = _decode_token(token)
            if payload.get('type') != 'access':
                return Response({'valid': False, 'error': 'invalid token type'}, status=status.HTTP_400_BAD_REQUEST)
            return Response({'valid': True, 'payload': payload})
        except Exception as e:
            return Response({'valid': False, 'error': str(e)}, status=status.HTTP_401_UNAUTHORIZED)


class MeView(APIView):
    def get(self, request):
        token = _extract_bearer(request)
        if not token:
            return Response({'error': 'Missing bearer token'}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            payload = _decode_token(token)
            user = UserAccount.objects.get(id=int(payload['sub']), is_active=True)
        except Exception:
            return Response({'error': 'Invalid token'}, status=status.HTTP_401_UNAUTHORIZED)

        return Response(UserSerializer(user).data)


class UserListView(APIView):
    def get(self, request):
        users = UserAccount.objects.all().order_by('-created_at', '-id')
        return Response(UserSerializer(users, many=True).data)


class HealthLiveView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        return Response({'status': 'live', 'service': 'auth-service'})


class HealthReadyView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        UserAccount.objects.count()
        return Response({'status': 'ready', 'service': 'auth-service'})
