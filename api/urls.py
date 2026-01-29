from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()

# User & Auth routes
router.register(r'profiles', views.UserProfileViewSet, basename='profile')
router.register(r'lawyers', views.LawyerProfileViewSet, basename='lawyer')

# Chatbot routes
router.register(r'legal-topics', views.LegalTopicViewSet, basename='legaltopic')
router.register(r'chat-sessions', views.ChatSessionViewSet, basename='chatsession')

# Appointment routes
router.register(r'appointments', views.AppointmentViewSet, basename='appointment')

# Educational routes
router.register(r'course-categories', views.CourseCategoryViewSet, basename='coursecategory')
router.register(r'courses', views.CourseViewSet, basename='course')
router.register(r'user-progress', views.UserProgressViewSet, basename='userprogress')

# Document routes
router.register(r'document-categories', views.DocumentCategoryViewSet, basename='documentcategory')
router.register(r'document-templates', views.DocumentTemplateViewSet, basename='documenttemplate')
router.register(r'generated-documents', views.GeneratedDocumentViewSet, basename='generateddocument')

# Payment routes
router.register(r'subscription-plans', views.SubscriptionPlanViewSet, basename='subscriptionplan')
router.register(r'payments', views.PaymentViewSet, basename='payment')

# Notification routes
router.register(r'notifications', views.NotificationViewSet, basename='notification')

urlpatterns = [
    # Auth endpoints
    path('auth/register/', views.RegisterView.as_view(), name='register'),
    path('auth/login/', views.LoginView.as_view(), name='login'),
    path('auth/logout/', views.LogoutView.as_view(), name='logout'),
    path('auth/me/', views.CurrentUserView.as_view(), name='current-user'),
    path('auth/change-password/', views.ChangePasswordView.as_view(), name='change-password'),
    
    # Dashboard
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('admin/dashboard/', views.AdminDashboardView.as_view(), name='admin-dashboard'),
    
    # Public endpoints
    path('health/', views.health_check, name='health-check'),
    path('stats/', views.public_stats, name='public-stats'),
    
    # Include router URLs
    path('', include(router.urls)),
]