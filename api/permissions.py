from rest_framework import permissions
from django.utils import timezone

class IsPremiumUser(permissions.BasePermission):
    """Permissão apenas para usuários premium"""
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_premium

class IsLawyer(permissions.BasePermission):
    """Permissão apenas para advogados"""
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_lawyer

class IsOwnerOrReadOnly(permissions.BasePermission):
    """Permissão para dono ou apenas leitura"""
    
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Verificar se o usuário é o dono do objeto
        if hasattr(obj, 'user'):
            return obj.user == request.user
        elif hasattr(obj, 'owner'):
            return obj.owner == request.user
        
        return False

class IsAdminOrReadOnly(permissions.BasePermission):
    """Permissão para admin ou apenas leitura"""
    
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        
        return request.user and request.user.is_staff

class HasSubscription(permissions.BasePermission):
    """Permissão baseada no tipo de assinatura"""
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Verificar se a assinatura está ativa
        if not request.user.subscription_end:
            return False
        
        return timezone.now() < request.user.subscription_end