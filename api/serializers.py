from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.utils import timezone
from datetime import timedelta
import uuid
from .models import *

# ==================== USER SERIALIZERS ====================

class UserSerializer(serializers.ModelSerializer):
    is_premium = serializers.BooleanField(read_only=True)
    has_lawyer_profile = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'full_name', 'phone', 'plan_type',
            'is_premium', 'is_lawyer', 'lawyer_specialization',
            'oab_number', 'has_lawyer_profile', 'date_joined'
        ]
        read_only_fields = ['id', 'date_joined', 'is_premium', 'has_lawyer_profile']

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = User
        fields = ['email', 'full_name', 'phone', 'password', 'password2']
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "As senhas não coincidem."})
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(**validated_data)
        UserProfile.objects.create(user=user)
        return user

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True)
    
    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        
        user = authenticate(username=email, password=password)
        if not user:
            raise serializers.ValidationError("Credenciais inválidas")
        
        if not user.is_active:
            raise serializers.ValidationError("Conta desativada")
        
        attrs['user'] = user
        return attrs

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    confirm_password = serializers.CharField(required=True)
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"new_password": "As senhas não coincidem."})
        return attrs
    
    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Senha atual incorreta")
        return value
    
    def save(self, **kwargs):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user

# ==================== PROFILE SERIALIZERS ====================

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = '__all__'
        read_only_fields = ['user', 'created_at', 'updated_at']

class LawyerProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    full_name = serializers.CharField(source='user.full_name', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    phone = serializers.CharField(source='user.phone', read_only=True)
    
    class Meta:
        model = LawyerProfile
        fields = '__all__'
        read_only_fields = ['user', 'rating', 'total_reviews', 'created_at', 'updated_at']

# ==================== CHATBOT SERIALIZERS ====================

class LegalTopicSerializer(serializers.ModelSerializer):
    class Meta:
        model = LegalTopic
        fields = '__all__'

class ChatSessionSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    message_count = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    
    class Meta:
        model = ChatSession
        fields = ['id', 'title', 'topic', 'user', 'language', 'created_at', 
                 'updated_at', 'is_active', 'message_count', 'last_message']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']
    
    def get_message_count(self, obj):
        return obj.messages.count()
    
    def get_last_message(self, obj):
        last_message = obj.messages.last()
        if last_message:
            return {
                'content': last_message.content[:100],
                'sender': last_message.sender_type,
                'time': last_message.created_at
            }
        return None

class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = '__all__'
        read_only_fields = ['id', 'session', 'created_at']

class ChatMessageCreateSerializer(serializers.Serializer):
    content = serializers.CharField(required=True, max_length=5000)
    session_id = serializers.UUIDField(required=False)

# ==================== APPOINTMENT SERIALIZERS ====================

class AvailabilitySerializer(serializers.ModelSerializer):
    lawyer_name = serializers.CharField(source='lawyer.user.full_name', read_only=True)
    
    class Meta:
        model = Availability
        fields = '__all__'

class AppointmentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    lawyer = LawyerProfileSerializer(read_only=True)
    lawyer_name = serializers.CharField(source='lawyer.user.full_name', read_only=True)
    user_name = serializers.CharField(source='user.full_name', read_only=True)
    
    class Meta:
        model = Appointment
        fields = '__all__'
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']

class AppointmentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = ['lawyer', 'scheduled_date', 'duration', 'consultation_type', 'notes', 'location']
    
    def validate(self, attrs):
        # Verificar se o advogado está disponível
        lawyer = attrs.get('lawyer')
        scheduled_date = attrs.get('scheduled_date')
        
        # Verificar se o usuário tem plano premium para múltiplos agendamentos
        user = self.context['request'].user
        if not user.is_premium:
            active_appointments = Appointment.objects.filter(
                user=user,
                status__in=['pending', 'confirmed']
            ).count()
            
            if active_appointments >= 2:
                raise serializers.ValidationError(
                    "Limite de agendamentos ativos atingido. Atualize para Premium."
                )
        
        return attrs

# ==================== EDUCATIONAL SERIALIZERS ====================

class CourseCategorySerializer(serializers.ModelSerializer):
    course_count = serializers.SerializerMethodField()
    
    class Meta:
        model = CourseCategory
        fields = '__all__'
    
    def get_course_count(self, obj):
        return obj.courses.filter(is_active=True).count()

class CourseSerializer(serializers.ModelSerializer):
    category = CourseCategorySerializer(read_only=True)
    category_id = serializers.UUIDField(write_only=True)
    lesson_count = serializers.SerializerMethodField()
    enrolled_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Course
        fields = '__all__'
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at']
    
    def get_lesson_count(self, obj):
        return obj.lessons.count()
    
    def get_enrolled_count(self, obj):
        return obj.user_progress.count()

class LessonSerializer(serializers.ModelSerializer):
    course_title = serializers.CharField(source='course.title', read_only=True)
    
    class Meta:
        model = Lesson
        fields = '__all__'
        read_only_fields = ['id', 'course', 'created_at', 'updated_at']

class UserProgressSerializer(serializers.ModelSerializer):
    course = CourseSerializer(read_only=True)
    lesson = LessonSerializer(read_only=True)
    
    class Meta:
        model = UserProgress
        fields = '__all__'
        read_only_fields = ['id', 'user', 'created_at', 'last_accessed']

# ==================== DOCUMENT SERIALIZERS ====================

class DocumentCategorySerializer(serializers.ModelSerializer):
    template_count = serializers.SerializerMethodField()
    
    class Meta:
        model = DocumentCategory
        fields = '__all__'
    
    def get_template_count(self, obj):
        return obj.templates.filter(is_active=True).count()

class DocumentTemplateSerializer(serializers.ModelSerializer):
    category = DocumentCategorySerializer(read_only=True)
    
    class Meta:
        model = DocumentTemplate
        fields = '__all__'
        read_only_fields = ['id', 'downloads_count', 'created_at', 'updated_at']

class GeneratedDocumentSerializer(serializers.ModelSerializer):
    template = DocumentTemplateSerializer(read_only=True)
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = GeneratedDocument
        fields = '__all__'
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']

class GenerateDocumentSerializer(serializers.Serializer):
    template_id = serializers.UUIDField(required=True)
    data = serializers.JSONField(required=True)

# ==================== PAYMENT SERIALIZERS ====================

class SubscriptionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        fields = '__all__'

class PaymentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    plan = SubscriptionPlanSerializer(read_only=True)
    
    class Meta:
        model = Payment
        fields = '__all__'
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']

class CreatePaymentSerializer(serializers.Serializer):
    plan_id = serializers.UUIDField(required=True)
    payment_method = serializers.ChoiceField(
        choices=Payment.PAYMENT_METHOD_CHOICES,
        required=True
    )
    
    def validate(self, attrs):
        try:
            plan = SubscriptionPlan.objects.get(id=attrs['plan_id'], is_active=True)
            attrs['plan'] = plan
        except SubscriptionPlan.DoesNotExist:
            raise serializers.ValidationError({"plan_id": "Plano não encontrado ou inativo."})
        
        return attrs

# ==================== DASHBOARD SERIALIZERS ====================

class DashboardStatsSerializer(serializers.Serializer):
    total_appointments = serializers.IntegerField()
    active_appointments = serializers.IntegerField()
    chat_sessions = serializers.IntegerField()
    courses_enrolled = serializers.IntegerField()
    documents_generated = serializers.IntegerField()
    is_premium = serializers.BooleanField()
    subscription_end = serializers.DateTimeField(allow_null=True)
    recent_activity = serializers.ListField(child=serializers.DictField())

# ==================== UTILITY SERIALIZERS ====================

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = '__all__'
        read_only_fields = ['id', 'user', 'created_at']

class AuditLogSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True, allow_null=True)
    
    class Meta:
        model = AuditLog
        fields = '__all__'
        read_only_fields = ['id', 'created_at']