from rest_framework import viewsets, status, generics
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.contrib.auth import authenticate
from django.utils import timezone
from datetime import datetime, timedelta
import json
import math
from django.db.models import Q
import uuid

from .models import User, Session, Location, Announcement, UserProfile, SavedAnnouncement, ViewedAnnouncement
from .serializers import (
    UserSerializer, SessionSerializer, LocationSerializer, 
    AnnouncementSerializer, AnnouncementRequestSerializer,
    UserProfileSerializer, AuthSerializer, AuthResponseSerializer,
    LocationRequestSerializer
)
from .utils import validate_session, get_user_from_session

class AuthViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]
    
    @action(detail=False, methods=['post'], url_path='register')
    def register(self, request):
        serializer = AuthSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        username = serializer.validated_data['username']
        password = serializer.validated_data['password']
        
        if User.objects.filter(username=username).exists():
            return Response(
                {"error": "Username already exists"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user = User.objects.create_user(username=username, password=password)
        
        session = Session.objects.create(
            user=user,
            expires_at=timezone.now() + timedelta(days=7),
            token=str(uuid.uuid4())
        )
        
        response_serializer = AuthResponseSerializer({
            'sessionId': session.token, 
            'username': user.username
        })
        
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['post'], url_path='login')
    def login(self, request):
        serializer = AuthSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        username = serializer.validated_data['username']
        password = serializer.validated_data['password']
        
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response(
                {"error": "Invalid credentials"}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        if not user.check_password(password):
            return Response(
                {"error": "Invalid credentials"}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        session = Session.objects.create(
            user=user,
            expires_at=timezone.now() + timedelta(days=7),
            token=str(uuid.uuid4())
        )
        
        response_serializer = AuthResponseSerializer({
            'sessionId': session.token,  # Envia o token
            'username': user.username
        })
        
        return Response(response_serializer.data, status=status.HTTP_200_OK)
