# api/serializers.py
from rest_framework import serializers
from .models import (
    User,
    Session, 
    Location, 
    Announcement, 
    UserProfile, 
    SavedAnnouncement, 
    ViewedAnnouncement
)

class AuthSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

class AuthResponseSerializer(serializers.Serializer):
    sessionId = serializers.CharField()
    username = serializers.CharField()

class SessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Session
        fields = ['id', 'user', 'expires_at', 'created_at']

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']

class LocationSerializer(serializers.ModelSerializer):
    ownerUsername = serializers.CharField(source='owner.username', read_only=True)
    
    class Meta:
        model = Location
        fields = [
            'id', 'name', 'type', 'latitude', 'longitude',
            'radius_meters', 'wifi_ids_csv', 'ownerUsername',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'ownerUsername']

class LocationRequestSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=200)
    type = serializers.CharField(max_length=50)
    latitude = serializers.FloatField(required=False, allow_null=True)
    longitude = serializers.FloatField(required=False, allow_null=True)
    radius_meters = serializers.FloatField(required=False, default=100.0)
    wifi_ids_csv = serializers.CharField(required=False, allow_blank=True)

class AnnouncementSerializer(serializers.ModelSerializer):
    # Correção definitiva: Forçar o nome do campo para camelCase
    ownerUsername = serializers.CharField(source='owner.username', read_only=True)
    location = LocationSerializer(read_only=True)
    
    class Meta:
        model = Announcement
        fields = [
            'id', 'title', 'content', 'ownerUsername', 'location',
            'policy_type', 'profile_restrictions_json', 'start_time',
            'end_time', 'delivery_mode', 'is_active', 'view_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'is_active', 'view_count',
            'created_at', 'updated_at'
        ]

class AnnouncementRequestSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255)
    content = serializers.CharField()
    location_id = serializers.IntegerField(required=False)
    policy_type = serializers.ChoiceField(
        choices=Announcement.POLICY_TYPES, 
        required=False, 
        default='WHITELIST'
    )
    profile_restrictions_json = serializers.CharField(required=False, allow_blank=True)
    start_time = serializers.DateTimeField(required=False)
    end_time = serializers.DateTimeField(required=False, allow_null=True)
    delivery_mode = serializers.ChoiceField(
        choices=Announcement.DELIVERY_MODES, 
        required=False, 
        default='CENTRALIZED'
    )
    
    def validate(self, data):
        location_id = data.get('location_id')
        if location_id:
            try:
                location = Location.objects.get(id=location_id)
                data['location'] = location
            except Location.DoesNotExist:
                raise serializers.ValidationError(
                    {"location_id": "Location not found"}
                )
        else:
            raise serializers.ValidationError(
                {"location_id": "Location ID is required"}
            )
        
        return data

class UserProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    
    class Meta:
        model = UserProfile
        fields = ['id', 'username', 'email', 'key', 'value', 'created_at', 'updated_at']
        read_only_fields = ['id', 'username', 'email', 'created_at', 'updated_at']

class SavedAnnouncementSerializer(serializers.ModelSerializer):
    announcement = AnnouncementSerializer(read_only=True)
    
    class Meta:
        model = SavedAnnouncement
        fields = ['id', 'announcement', 'saved_at']

class ViewedAnnouncementSerializer(serializers.ModelSerializer):
    announcement = AnnouncementSerializer(read_only=True)
    
    class Meta:
        model = ViewedAnnouncement
        fields = ['id', 'announcement', 'viewed_at']
