from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .models import User, UserProfile, Notification

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
        
        # Enviar notificação de boas-vindas
        Notification.objects.create(
            user=instance,
            title='Bem-vindo ao Juridicando!',
            message='Sua conta foi criada com sucesso. Explore nossos recursos jurídicos.',
            notification_type='info'
        )

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    try:
        instance.profile.save()
    except UserProfile.DoesNotExist:
        UserProfile.objects.create(user=instance)