from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import *

class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'full_name', 'plan_type', 'is_premium', 'is_lawyer', 'is_staff', 'is_active')
    list_filter = ('plan_type', 'is_lawyer', 'is_staff', 'is_active', 'date_joined')
    search_fields = ('email', 'full_name', 'phone')
    ordering = ('-date_joined',)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Informações Pessoais', {'fields': ('full_name', 'phone')}),
        ('Assinatura', {'fields': ('plan_type', 'subscription_start', 'subscription_end')}),
        ('Advogado', {'fields': ('is_lawyer', 'lawyer_specialization', 'oab_number')}),
        ('Permissões', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Datas Importantes', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'full_name', 'password1', 'password2'),
        }),
    )

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'city', 'country', 'created_at')
    search_fields = ('user__email', 'user__full_name', 'city', 'country')

@admin.register(LawyerProfile)
class LawyerProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'experience_years', 'hourly_rate', 'rating', 'is_verified', 'is_available')
    list_filter = ('is_verified', 'is_available', 'experience_years')
    search_fields = ('user__email', 'user__full_name', 'bio', 'specializations')

@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'topic', 'created_at', 'updated_at', 'is_active')
    list_filter = ('is_active', 'created_at', 'topic')
    search_fields = ('user__email', 'title', 'topic__name')

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('user', 'lawyer', 'scheduled_date', 'status', 'consultation_type', 'created_at')
    list_filter = ('status', 'consultation_type', 'scheduled_date')
    search_fields = ('user__email', 'lawyer__user__email', 'notes')

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'difficulty', 'is_premium', 'price', 'is_active')
    list_filter = ('category', 'difficulty', 'is_premium', 'is_active')
    search_fields = ('title', 'description', 'category__name')
    prepopulated_fields = {'slug': ('title',)}

@admin.register(DocumentTemplate)
class DocumentTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'is_premium', 'price', 'downloads_count', 'is_active')
    list_filter = ('category', 'is_premium', 'is_active')
    search_fields = ('name', 'description', 'category__name')

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan', 'amount', 'status', 'payment_method', 'payment_date')
    list_filter = ('status', 'payment_method', 'payment_date')
    search_fields = ('user__email', 'transaction_id', 'plan__name')

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'notification_type', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('user__email', 'title', 'message')

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'model_name', 'created_at')
    list_filter = ('action', 'model_name', 'created_at')
    search_fields = ('user__email', 'details', 'ip_address')

# Registrar outros modelos
admin.site.register(User, UserAdmin)
admin.site.register(LegalTopic)
admin.site.register(ChatMessage)
admin.site.register(Availability)
admin.site.register(CourseCategory)
admin.site.register(Lesson)
admin.site.register(UserProgress)
admin.site.register(DocumentCategory)
admin.site.register(GeneratedDocument)
admin.site.register(SubscriptionPlan)