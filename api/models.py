from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
import uuid

# ==================== USER MANAGEMENT ====================

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('O email é obrigatório')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        
        return self.create_user(email, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20, blank=True, null=True)
    
    # Subscription plans
    PLAN_CHOICES = [
        ('free', 'Gratuito'),
        ('premium', 'Premium'),
        ('professional', 'Profissional'),
    ]
    plan_type = models.CharField(max_length=20, choices=PLAN_CHOICES, default='free')
    subscription_start = models.DateTimeField(null=True, blank=True)
    subscription_end = models.DateTimeField(null=True, blank=True)
    
    # User roles
    is_lawyer = models.BooleanField(default=False)
    lawyer_specialization = models.CharField(max_length=100, blank=True, null=True)
    oab_number = models.CharField(max_length=50, blank=True, null=True)
    
    # System fields
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(default=timezone.now)
    last_login = models.DateTimeField(null=True, blank=True)
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name']
    
    def __str__(self):
        return f"{self.full_name} ({self.email})"
    
    @property
    def is_premium(self):
        if self.plan_type == 'free':
            return False
        if not self.subscription_end:
            return False
        return timezone.now() < self.subscription_end
    
    class Meta:
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'
        ordering = ['-date_joined']

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    language = models.CharField(max_length=10, default='pt')
    notifications_enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Perfil de {self.user.full_name}"
    
    class Meta:
        verbose_name = 'Perfil de Usuário'
        verbose_name_plural = 'Perfis de Usuários'

# ==================== LEGAL CHATBOT ====================

class LegalTopic(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=100)
    keywords = models.JSONField(default=list, blank=True)
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = 'Tópico Legal'
        verbose_name_plural = 'Tópicos Legais'
        ordering = ['order', 'name']

class ChatSession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_sessions')
    title = models.CharField(max_length=200, blank=True, null=True)
    topic = models.ForeignKey(LegalTopic, on_delete=models.SET_NULL, null=True, blank=True)
    language = models.CharField(max_length=10, default='pt')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"Chat: {self.title or 'Sem título'} - {self.user.email}"
    
    class Meta:
        verbose_name = 'Sessão de Chat'
        verbose_name_plural = 'Sessões de Chat'
        ordering = ['-updated_at']

class ChatMessage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    sender_type = models.CharField(max_length=20, choices=[
        ('user', 'Usuário'),
        ('assistant', 'Assistente IA'),
    ])
    content = models.TextField()
    legal_references = models.JSONField(default=list, blank=True)
    confidence_score = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.sender_type}: {self.content[:50]}..."
    
    class Meta:
        verbose_name = 'Mensagem de Chat'
        verbose_name_plural = 'Mensagens de Chat'
        ordering = ['created_at']

# ==================== LAWYER APPOINTMENTS ====================

class LawyerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='lawyer_profile')
    bio = models.TextField()
    experience_years = models.IntegerField(default=0)
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2)
    rating = models.FloatField(default=0.0)
    total_reviews = models.IntegerField(default=0)
    languages = models.JSONField(default=list)
    consultation_types = models.JSONField(default=list)  # ['online', 'in_person']
    specializations = models.JSONField(default=list)
    education = models.JSONField(default=list)  # Lista de formações
    certifications = models.JSONField(default=list)
    is_verified = models.BooleanField(default=False)
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Advogado: {self.user.full_name}"
    
    class Meta:
        verbose_name = 'Perfil de Advogado'
        verbose_name_plural = 'Perfis de Advogados'

class Availability(models.Model):
    DAY_CHOICES = [
        (0, 'Segunda-feira'),
        (1, 'Terça-feira'),
        (2, 'Quarta-feira'),
        (3, 'Quinta-feira'),
        (4, 'Sexta-feira'),
        (5, 'Sábado'),
        (6, 'Domingo'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lawyer = models.ForeignKey(LawyerProfile, on_delete=models.CASCADE, related_name='availabilities')
    day_of_week = models.IntegerField(choices=DAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_recurring = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.lawyer.user.full_name} - {self.get_day_of_week_display()} {self.start_time}-{self.end_time}"
    
    class Meta:
        verbose_name = 'Disponibilidade'
        verbose_name_plural = 'Disponibilidades'
        ordering = ['day_of_week', 'start_time']

class Appointment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pendente'),
        ('confirmed', 'Confirmado'),
        ('completed', 'Concluído'),
        ('cancelled', 'Cancelado'),
        ('no_show', 'Não Compareceu'),
    ]
    
    CONSULTATION_TYPES = [
        ('online', 'Online'),
        ('in_person', 'Presencial'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='appointments')
    lawyer = models.ForeignKey(LawyerProfile, on_delete=models.CASCADE, related_name='appointments')
    scheduled_date = models.DateTimeField()
    duration = models.IntegerField(default=60)  # em minutos
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    consultation_type = models.CharField(max_length=20, choices=CONSULTATION_TYPES)
    notes = models.TextField(blank=True, null=True)
    meeting_link = models.URLField(blank=True, null=True)
    location = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Consulta: {self.user.full_name} com {self.lawyer.user.full_name}"
    
    class Meta:
        verbose_name = 'Consulta'
        verbose_name_plural = 'Consultas'
        ordering = ['-scheduled_date']

# ==================== EDUCATIONAL PLATFORM ====================

class CourseCategory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    description = models.TextField()
    icon = models.CharField(max_length=50, blank=True, null=True)
    color = models.CharField(max_length=20, default='#4F46E5')
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = 'Categoria de Curso'
        verbose_name_plural = 'Categorias de Cursos'
        ordering = ['order', 'name']

class Course(models.Model):
    DIFFICULTY_CHOICES = [
        ('beginner', 'Iniciante'),
        ('intermediate', 'Intermediário'),
        ('advanced', 'Avançado'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField()
    short_description = models.CharField(max_length=300)
    category = models.ForeignKey(CourseCategory, on_delete=models.SET_NULL, null=True, related_name='courses')
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='beginner')
    duration_hours = models.IntegerField(default=1)
    thumbnail = models.ImageField(upload_to='course_thumbnails/', blank=True, null=True)
    is_premium = models.BooleanField(default=False)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title
    
    class Meta:
        verbose_name = 'Curso'
        verbose_name_plural = 'Cursos'
        ordering = ['title']

class Lesson(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=200)
    content = models.TextField()
    video_url = models.URLField(blank=True, null=True)
    duration_minutes = models.IntegerField(default=15)
    order = models.IntegerField(default=0)
    is_free_preview = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.course.title} - {self.title}"
    
    class Meta:
        verbose_name = 'Lição'
        verbose_name_plural = 'Lições'
        ordering = ['order']

class UserProgress(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='progress')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='user_progress')
    lesson = models.ForeignKey(Lesson, on_delete=models.SET_NULL, null=True, blank=True)
    completed = models.BooleanField(default=False)
    progress_percentage = models.IntegerField(default=0)
    last_accessed = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.email} - {self.course.title}: {self.progress_percentage}%"
    
    class Meta:
        verbose_name = 'Progresso do Usuário'
        verbose_name_plural = 'Progressos dos Usuários'
        unique_together = ['user', 'course']

# ==================== DOCUMENT GENERATION ====================

class DocumentCategory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    description = models.TextField()
    icon = models.CharField(max_length=50, blank=True, null=True)
    order = models.IntegerField(default=0)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = 'Categoria de Documento'
        verbose_name_plural = 'Categorias de Documentos'
        ordering = ['order', 'name']

class DocumentTemplate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey(DocumentCategory, on_delete=models.SET_NULL, null=True, related_name='templates')
    template_file = models.FileField(upload_to='document_templates/', blank=True, null=True)
    template_html = models.TextField(blank=True, null=True)
    is_premium = models.BooleanField(default=False)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    fields_schema = models.JSONField()  # Schema dos campos do formulário
    sample_data = models.JSONField(default=dict, blank=True)
    downloads_count = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = 'Modelo de Documento'
        verbose_name_plural = 'Modelos de Documentos'
        ordering = ['name']

class GeneratedDocument(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='documents')
    template = models.ForeignKey(DocumentTemplate, on_delete=models.CASCADE, related_name='generated_docs')
    document_data = models.JSONField()  # Dados preenchidos pelo usuário
    generated_file = models.FileField(upload_to='generated_documents/', blank=True, null=True)
    status = models.CharField(max_length=20, choices=[
        ('draft', 'Rascunho'),
        ('generated', 'Gerado'),
        ('downloaded', 'Baixado'),
    ], default='draft')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.template.name} - {self.user.full_name}"
    
    class Meta:
        verbose_name = 'Documento Gerado'
        verbose_name_plural = 'Documentos Gerados'
        ordering = ['-created_at']

# ==================== PAYMENT & SUBSCRIPTIONS ====================

class SubscriptionPlan(models.Model):
    PERIOD_CHOICES = [
        ('monthly', 'Mensal'),
        ('yearly', 'Anual'),
        ('lifetime', 'Vitalício'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    period = models.CharField(max_length=20, choices=PERIOD_CHOICES, default='monthly')
    features = models.JSONField(default=list)
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} - {self.price}€/{self.period}"
    
    class Meta:
        verbose_name = 'Plano de Assinatura'
        verbose_name_plural = 'Planos de Assinatura'
        ordering = ['order', 'price']

class Payment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pendente'),
        ('completed', 'Completo'),
        ('failed', 'Falhou'),
        ('refunded', 'Reembolsado'),
        ('cancelled', 'Cancelado'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('credit_card', 'Cartão de Crédito'),
        ('debit_card', 'Cartão de Débito'),
        ('mbway', 'MBWay'),
        ('bank_transfer', 'Transferência Bancária'),
        ('paypal', 'PayPal'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.SET_NULL, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='EUR')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    payment_date = models.DateTimeField(null=True, blank=True)
    subscription_start = models.DateTimeField(null=True, blank=True)
    subscription_end = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Pagamento {self.transaction_id} - {self.user.email}"
    
    class Meta:
        verbose_name = 'Pagamento'
        verbose_name_plural = 'Pagamentos'
        ordering = ['-created_at']

# ==================== UTILITY MODELS ====================

class Notification(models.Model):
    TYPE_CHOICES = [
        ('info', 'Informação'),
        ('success', 'Sucesso'),
        ('warning', 'Aviso'),
        ('error', 'Erro'),
        ('appointment', 'Consulta'),
        ('payment', 'Pagamento'),
        ('system', 'Sistema'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='info')
    is_read = models.BooleanField(default=False)
    action_url = models.URLField(blank=True, null=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.title} - {self.user.email}"
    
    class Meta:
        verbose_name = 'Notificação'
        verbose_name_plural = 'Notificações'
        ordering = ['-created_at']

class AuditLog(models.Model):
    ACTION_CHOICES = [
        ('create', 'Criar'),
        ('update', 'Atualizar'),
        ('delete', 'Excluir'),
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('payment', 'Pagamento'),
        ('download', 'Download'),
        ('access', 'Acesso'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_logs')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=100)
    object_id = models.CharField(max_length=100)
    details = models.TextField(blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.email if self.user else 'System'} - {self.action} - {self.model_name}"
    
    class Meta:
        verbose_name = 'Log de Auditoria'
        verbose_name_plural = 'Logs de Auditoria'
        ordering = ['-created_at']