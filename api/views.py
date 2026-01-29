from rest_framework import viewsets, status, generics, permissions, filters
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from django.contrib.auth import authenticate, login, logout
from django.utils import timezone
from datetime import timedelta
import uuid
from django.db.models import Q, Count, F
from django.shortcuts import get_object_or_404
from django.core.paginator import Paginator

from .models import *
from .serializers import *
from .permissions import IsPremiumUser, IsLawyer, IsOwnerOrReadOnly

# ==================== AUTHENTICATION VIEWS ====================

class RegisterView(generics.CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Criar token de autenticação
        token, created = Token.objects.get_or_create(user=user)
        
        # Criar log de auditoria
        AuditLog.objects.create(
            user=user,
            action='create',
            model_name='User',
            object_id=str(user.id),
            details='Novo usuário registrado',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        return Response({
            'token': token.key,
            'user': UserSerializer(user).data,
            'message': 'Registro realizado com sucesso!'
        }, status=status.HTTP_201_CREATED)

class LoginView(ObtainAuthToken):
    permission_classes = [AllowAny]
    
    def post(self, request, *args, **kwargs):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            
            # Criar ou obter token
            token, created = Token.objects.get_or_create(user=user)
            
            # Atualizar último login
            user.last_login = timezone.now()
            user.save()
            
            # Criar log de auditoria
            AuditLog.objects.create(
                user=user,
                action='login',
                model_name='User',
                object_id=str(user.id),
                details='Usuário fez login',
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            return Response({
                'token': token.key,
                'user': UserSerializer(user).data,
                'message': 'Login realizado com sucesso!'
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            request.user.auth_token.delete()
            
            # Criar log de auditoria
            AuditLog.objects.create(
                user=request.user,
                action='logout',
                model_name='User',
                object_id=str(request.user.id),
                details='Usuário fez logout',
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
        except:
            pass
        
        return Response({'message': 'Logout realizado com sucesso!'})

class CurrentUserView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer
    
    def get_object(self):
        return self.request.user
    
    def retrieve(self, request, *args, **kwargs):
        user = self.get_object()
        serializer = self.get_serializer(user)
        
        # Adicionar informações do perfil
        profile_data = {}
        try:
            profile = user.profile
            profile_data = UserProfileSerializer(profile).data
        except UserProfile.DoesNotExist:
            pass
        
        response_data = serializer.data
        response_data['profile'] = profile_data
        
        return Response(response_data)

class ChangePasswordView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ChangePasswordSerializer
    
    def get_object(self):
        return self.request.user
    
    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Criar log de auditoria
        AuditLog.objects.create(
            user=user,
            action='update',
            model_name='User',
            object_id=str(user.id),
            details='Senha alterada',
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        return Response({'message': 'Senha alterada com sucesso!'})

# ==================== USER PROFILE VIEWS ====================

class UserProfileViewSet(viewsets.ModelViewSet):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return UserProfile.objects.filter(user=self.request.user)
    
    def get_object(self):
        return get_object_or_404(UserProfile, user=self.request.user)
    
    def perform_update(self, serializer):
        instance = serializer.save()
        
        # Criar log de auditoria
        AuditLog.objects.create(
            user=self.request.user,
            action='update',
            model_name='UserProfile',
            object_id=str(instance.id),
            details='Perfil atualizado',
            ip_address=self.request.META.get('REMOTE_ADDR')
        )
    
    @action(detail=False, methods=['post'])
    def become_lawyer(self, request):
        user = request.user
        
        # Verificar se já é advogado
        if hasattr(user, 'lawyer_profile'):
            return Response(
                {'error': 'Você já tem um perfil de advogado'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = LawyerProfileSerializer(data=request.data)
        if serializer.is_valid():
            # Atualizar usuário
            user.is_lawyer = True
            user.lawyer_specialization = serializer.validated_data.get('specializations', [])[0] if serializer.validated_data.get('specializations') else None
            user.save()
            
            # Criar perfil de advogado
            lawyer_profile = serializer.save(user=user)
            
            # Criar log de auditoria
            AuditLog.objects.create(
                user=user,
                action='create',
                model_name='LawyerProfile',
                object_id=str(lawyer_profile.id),
                details='Perfil de advogado criado',
                ip_address=request.META.get('REMOTE_ADDR')
            )
            
            return Response(LawyerProfileSerializer(lawyer_profile).data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# ==================== LEGAL CHATBOT VIEWS ====================

class LegalTopicViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [AllowAny]
    serializer_class = LegalTopicSerializer
    queryset = LegalTopic.objects.filter(is_active=True)
    
    @action(detail=False, methods=['get'])
    def categories(self, request):
        categories = LegalTopic.objects.filter(is_active=True).values_list('category', flat=True).distinct()
        return Response({'categories': list(categories)})

class ChatSessionViewSet(viewsets.ModelViewSet):
    serializer_class = ChatSessionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return ChatSession.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
        
        # Criar log de auditoria
        AuditLog.objects.create(
            user=self.request.user,
            action='create',
            model_name='ChatSession',
            object_id=str(serializer.instance.id),
            details='Nova sessão de chat criada',
            ip_address=self.request.META.get('REMOTE_ADDR')
        )
    
    @action(detail=True, methods=['post'])
    def send_message(self, request, pk=None):
        session = self.get_object()
        
        # Verificar limites para usuários free
        if not request.user.is_premium:
            today = timezone.now().date()
            messages_today = ChatMessage.objects.filter(
                session__user=request.user,
                created_at__date=today,
                sender_type='user'
            ).count()
            
            if messages_today >= 5:  # Limite de 5 mensagens por dia
                return Response(
                    {'error': 'Limite de mensagens diárias atingido. Atualize para Premium.'},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        serializer = ChatMessageCreateSerializer(data=request.data)
        if serializer.is_valid():
            content = serializer.validated_data['content']
            
            # Salvar mensagem do usuário
            user_message = ChatMessage.objects.create(
                session=session,
                sender_type='user',
                content=content
            )
            
            # Gerar resposta simulada da IA
            ai_response = self.generate_ai_response(content, session)
            
            # Salvar resposta da IA
            ai_message = ChatMessage.objects.create(
                session=session,
                sender_type='assistant',
                content=ai_response['response'],
                legal_references=ai_response.get('references', []),
                confidence_score=ai_response.get('confidence', 0.8)
            )
            
            # Atualizar timestamp da sessão
            session.updated_at = timezone.now()
            session.save()
            
            return Response({
                'user_message': ChatMessageSerializer(user_message).data,
                'ai_response': ChatMessageSerializer(ai_message).data
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def generate_ai_response(self, user_message, session):
        """Função simulada para gerar resposta da IA"""
        # Em produção, integraria com Hugging Face Transformers
        
        # Palavras-chave para diferentes áreas do direito
        keywords = {
            'contrato': 'Direito Civil - Contratos',
            'divórcio': 'Direito de Família',
            'trabalho': 'Direito do Trabalho',
            'consumidor': 'Direito do Consumidor',
            'penal': 'Direito Penal',
            'imobiliário': 'Direito Imobiliário',
            'sucessões': 'Direito das Sucessões',
        }
        
        # Identificar área do direito baseada nas palavras-chave
        area = 'Direito Civil'  # padrão
        for key, value in keywords.items():
            if key in user_message.lower():
                area = value
                break
        
        # Respostas simuladas
        responses = {
            'Direito Civil': {
                'response': 'Baseado no Código Civil português, em particular nos artigos 405º a 486º que tratam dos contratos, recomendo que...',
                'references': [
                    {'code': 'Código Civil', 'article': '405º', 'title': 'Definição de contrato'},
                    {'code': 'Código Civil', 'article': '406º', 'title': 'Liberdade contratual'}
                ],
                'confidence': 0.85
            },
            'Direito de Família': {
                'response': 'Para questões de divórcio, o Código Civil estabelece os procedimentos nos artigos 1773º a 1796º. Considere também...',
                'references': [
                    {'code': 'Código Civil', 'article': '1773º', 'title': 'Divórcio por mútuo consentimento'},
                    {'code': 'Código Civil', 'article': '1774º', 'title': 'Divórcio sem consentimento'}
                ],
                'confidence': 0.9
            },
            'Direito do Trabalho': {
                'response': 'A legislação trabalhista portuguesa está principalmente no Código do Trabalho. Para sua questão específica...',
                'references': [
                    {'code': 'Código do Trabalho', 'article': '127º', 'title': 'Período experimental'},
                    {'code': 'Código do Trabalho', 'article': '394º', 'title': 'Despedimento'}
                ],
                'confidence': 0.8
            },
            'Direito do Consumidor': {
                'response': 'O Código do Consumidor (Decreto-Lei n.º 24/2014) protege os direitos dos consumidores. Neste caso...',
                'references': [
                    {'code': 'DL 24/2014', 'article': '5º', 'title': 'Direitos gerais do consumidor'},
                    {'code': 'DL 24/2014', 'article': '15º', 'title': 'Garantias'}
                ],
                'confidence': 0.75
            }
        }
        
        return responses.get(area, {
            'response': 'Para sua questão legal, recomendo consultar a legislação portuguesa aplicável e, se necessário, buscar orientação de um advogado especializado.',
            'references': [],
            'confidence': 0.6
        })
    
    @action(detail=True, methods=['get'])
    def messages(self, request, pk=None):
        session = self.get_object()
        messages = session.messages.all()
        serializer = ChatMessageSerializer(messages, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def close(self, request, pk=None):
        session = self.get_object()
        session.is_active = False
        session.save()
        return Response({'message': 'Sessão encerrada'})

# ==================== APPOINTMENT VIEWS ====================

class LawyerProfileViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [AllowAny]
    serializer_class = LawyerProfileSerializer
    queryset = LawyerProfile.objects.filter(is_available=True, is_verified=True)
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['user__full_name', 'specializations', 'bio']
    ordering_fields = ['rating', 'hourly_rate', 'experience_years']
    
    @action(detail=True, methods=['get'])
    def availability(self, request, pk=None):
        lawyer = self.get_object()
        date_str = request.query_params.get('date')
        
        if date_str:
            try:
                date = timezone.datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                return Response({'error': 'Formato de data inválido'}, status=400)
        else:
            date = timezone.now().date()
        
        # Calcular slots disponíveis
        slots = self.calculate_available_slots(lawyer, date)
        return Response({
            'lawyer': lawyer.user.full_name,
            'date': date,
            'available_slots': slots
        })
    
    def calculate_available_slots(self, lawyer, date):
        """Calcular slots disponíveis para um advogado em uma data específica"""
        slots = []
        
        # Verificar disponibilidades recorrentes
        day_of_week = date.weekday()
        availabilities = lawyer.availabilities.filter(
            day_of_week=day_of_week,
            is_active=True
        )
        
        for availability in availabilities:
            # Verificar se há agendamentos conflitantes
            start_datetime = timezone.datetime.combine(date, availability.start_time)
            end_datetime = timezone.datetime.combine(date, availability.end_time)
            
            # Criar slots de 30 minutos
            current = start_datetime
            while current + timedelta(minutes=30) <= end_datetime:
                # Verificar se não há agendamento neste horário
                conflicting = Appointment.objects.filter(
                    lawyer=lawyer,
                    scheduled_date__date=date,
                    scheduled_date__time__gte=current.time(),
                    scheduled_date__time__lt=(current + timedelta(minutes=30)).time(),
                    status__in=['pending', 'confirmed']
                ).exists()
                
                if not conflicting:
                    slots.append({
                        'start_time': current.time().strftime('%H:%M'),
                        'end_time': (current + timedelta(minutes=30)).time().strftime('%H:%M')
                    })
                
                current += timedelta(minutes=30)
        
        return slots

class AppointmentViewSet(viewsets.ModelViewSet):
    serializer_class = AppointmentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        if user.is_lawyer and hasattr(user, 'lawyer_profile'):
            # Advogado vê seus próprios agendamentos
            return Appointment.objects.filter(lawyer=user.lawyer_profile)
        else:
            # Usuário comum vê seus agendamentos
            return Appointment.objects.filter(user=user)
    
    def get_serializer_class(self):
        if self.action == 'create':
            return AppointmentCreateSerializer
        return AppointmentSerializer
    
    def perform_create(self, serializer):
        user = self.request.user
        
        # Verificar limites para usuários free
        if not user.is_premium:
            active_appointments = Appointment.objects.filter(
                user=user,
                status__in=['pending', 'confirmed']
            ).count()
            
            if active_appointments >= 1:
                raise serializers.ValidationError(
                    'Limite de agendamentos ativos atingido. Atualize para Premium.'
                )
        
        appointment = serializer.save(user=user)
        
        # Criar notificação
        Notification.objects.create(
            user=user,
            title='Consulta Agendada',
            message=f'Consulta agendada com {appointment.lawyer.user.full_name} para {appointment.scheduled_date.strftime("%d/%m/%Y %H:%M")}',
            notification_type='appointment',
            action_url=f'/appointments/{appointment.id}'
        )
        
        # Criar log de auditoria
        AuditLog.objects.create(
            user=user,
            action='create',
            model_name='Appointment',
            object_id=str(appointment.id),
            details='Nova consulta agendada',
            ip_address=self.request.META.get('REMOTE_ADDR')
        )
    
    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        appointment = self.get_object()
        
        # Apenas advogados podem confirmar consultas
        if not request.user.is_lawyer or not hasattr(request.user, 'lawyer_profile'):
            return Response(
                {'error': 'Apenas advogados podem confirmar consultas'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if appointment.lawyer != request.user.lawyer_profile:
            return Response(
                {'error': 'Esta consulta não pertence a você'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        appointment.status = 'confirmed'
        appointment.save()
        
        # Criar notificação para o usuário
        Notification.objects.create(
            user=appointment.user,
            title='Consulta Confirmada',
            message=f'Sua consulta com {appointment.lawyer.user.full_name} foi confirmada',
            notification_type='success',
            action_url=f'/appointments/{appointment.id}'
        )
        
        return Response({'message': 'Consulta confirmada com sucesso'})
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        appointment = self.get_object()
        
        # Verificar permissões
        if appointment.user != request.user and (
            not request.user.is_lawyer or 
            appointment.lawyer != request.user.lawyer_profile
        ):
            return Response(
                {'error': 'Você não tem permissão para cancelar esta consulta'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        appointment.status = 'cancelled'
        appointment.save()
        
        # Criar notificação
        other_user = appointment.lawyer.user if appointment.user == request.user else appointment.user
        Notification.objects.create(
            user=other_user,
            title='Consulta Cancelada',
            message=f'A consulta de {appointment.scheduled_date.strftime("%d/%m/%Y %H:%M")} foi cancelada',
            notification_type='warning'
        )
        
        return Response({'message': 'Consulta cancelada com sucesso'})

# ==================== EDUCATIONAL VIEWS ====================

class CourseCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [AllowAny]
    serializer_class = CourseCategorySerializer
    queryset = CourseCategory.objects.filter(is_active=True)

class CourseViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [AllowAny]
    serializer_class = CourseSerializer
    queryset = Course.objects.filter(is_active=True)
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description', 'category__name']
    ordering_fields = ['title', 'difficulty', 'price', 'created_at']
    
    @action(detail=True, methods=['get'])
    def lessons(self, request, pk=None):
        course = self.get_object()
        
        # Verificar acesso premium
        if course.is_premium and not request.user.is_authenticated:
            return Response(
                {'error': 'Login necessário para acessar este curso'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        if course.is_premium and not request.user.is_premium:
            return Response(
                {'error': 'Este curso requer assinatura Premium'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        lessons = course.lessons.all()
        serializer = LessonSerializer(lessons, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def enroll(self, request, pk=None):
        if not request.user.is_authenticated:
            return Response(
                {'error': 'Login necessário para se inscrever'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        course = self.get_object()
        
        # Verificar acesso premium
        if course.is_premium and not request.user.is_premium:
            return Response(
                {'error': 'Este curso requer assinatura Premium'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Criar ou obter progresso
        progress, created = UserProgress.objects.get_or_create(
            user=request.user,
            course=course,
            defaults={'progress_percentage': 0}
        )
        
        if created:
            # Criar notificação
            Notification.objects.create(
                user=request.user,
                title='Inscrição em Curso',
                message=f'Você se inscreveu no curso "{course.title}"',
                notification_type='success'
            )
            
            return Response(
                {'message': 'Inscrição realizada com sucesso'},
                status=status.HTTP_201_CREATED
            )
        else:
            return Response(
                {'message': 'Você já está inscrito neste curso'},
                status=status.HTTP_200_OK
            )

class UserProgressViewSet(viewsets.ModelViewSet):
    serializer_class = UserProgressSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return UserProgress.objects.filter(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def complete_lesson(self, request, pk=None):
        progress = self.get_object()
        lesson_id = request.data.get('lesson_id')
        
        try:
            lesson = Lesson.objects.get(id=lesson_id, course=progress.course)
            
            # Atualizar progresso
            progress.lesson = lesson
            progress.progress_percentage = self.calculate_progress(progress.course, request.user)
            progress.save()
            
            # Verificar se curso foi concluído
            if progress.progress_percentage >= 100:
                progress.completed = True
                progress.save()
                
                # Criar notificação
                Notification.objects.create(
                    user=request.user,
                    title='Curso Concluído',
                    message=f'Parabéns! Você concluiu o curso "{progress.course.title}"',
                    notification_type='success'
                )
            
            return Response({
                'progress_percentage': progress.progress_percentage,
                'completed': progress.completed
            })
        
        except Lesson.DoesNotExist:
            return Response(
                {'error': 'Lição não encontrada neste curso'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    def calculate_progress(self, course, user):
        """Calcular porcentagem de conclusão do curso"""
        total_lessons = course.lessons.count()
        if total_lessons == 0:
            return 0
        
        # Contar lições concluídas (baseado no progresso do usuário)
        completed_lessons = UserProgress.objects.filter(
            user=user,
            course=course,
            lesson__isnull=False
        ).count()
        
        return int((completed_lessons / total_lessons) * 100)

# ==================== DOCUMENT GENERATION VIEWS ====================

class DocumentCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [AllowAny]
    serializer_class = DocumentCategorySerializer
    queryset = DocumentCategory.objects.all()

class DocumentTemplateViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [AllowAny]
    serializer_class = DocumentTemplateSerializer
    
    def get_queryset(self):
        queryset = DocumentTemplate.objects.filter(is_active=True)
        
        # Para usuários não autenticados ou free, mostrar apenas templates gratuitos
        if not self.request.user.is_authenticated or not self.request.user.is_premium:
            queryset = queryset.filter(is_premium=False)
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def generate(self, request, pk=None):
        if not request.user.is_authenticated:
            return Response(
                {'error': 'Login necessário para gerar documentos'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        template = self.get_object()
        
        # Verificar acesso premium
        if template.is_premium and not request.user.is_premium:
            return Response(
                {'error': 'Este modelo requer assinatura Premium'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = GenerateDocumentSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data['data']
            
            # Criar documento gerado
            generated_doc = GeneratedDocument.objects.create(
                user=request.user,
                template=template,
                document_data=data,
                status='generated'
            )
            
            # Incrementar contador de downloads
            template.downloads_count += 1
            template.save()
            
            # Criar log de auditoria
            AuditLog.objects.create(
                user=request.user,
                action='create',
                model_name='GeneratedDocument',
                object_id=str(generated_doc.id),
                details=f'Documento gerado: {template.name}',
                ip_address=request.META.get('REMOTE_ADDR')
            )
            
            return Response({
                'message': 'Documento gerado com sucesso',
                'document_id': generated_doc.id,
                'document_name': template.name
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class GeneratedDocumentViewSet(viewsets.ModelViewSet):
    serializer_class = GeneratedDocumentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return GeneratedDocument.objects.filter(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def download(self, request, pk=None):
        document = self.get_object()
        
        if document.status != 'generated':
            return Response(
                {'error': 'Documento não gerado ainda'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Atualizar status
        document.status = 'downloaded'
        document.save()
        
        # Simular URL de download
        download_url = f'/api/documents/{document.id}/download/'
        
        return Response({
            'message': 'Download iniciado',
            'download_url': download_url,
            'document_name': document.template.name
        })

# ==================== PAYMENT VIEWS ====================

class SubscriptionPlanViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [AllowAny]
    serializer_class = SubscriptionPlanSerializer
    queryset = SubscriptionPlan.objects.filter(is_active=True)

class PaymentViewSet(viewsets.ModelViewSet):
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Payment.objects.filter(user=self.request.user)
    
    def get_serializer_class(self):
        if self.action == 'create':
            return CreatePaymentSerializer
        return PaymentSerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        plan = serializer.validated_data['plan']
        payment_method = serializer.validated_data['payment_method']
        
        # Calcular data de término da assinatura
        subscription_end = timezone.now()
        if plan.period == 'monthly':
            subscription_end += timedelta(days=30)
        elif plan.period == 'yearly':
            subscription_end += timedelta(days=365)
        else:  # lifetime
            subscription_end += timedelta(days=365 * 100)  # 100 anos
        
        # Criar pagamento (simulado)
        payment = Payment.objects.create(
            user=request.user,
            plan=plan,
            amount=plan.price,
            payment_method=payment_method,
            status='completed',
            transaction_id=f"TXN-{uuid.uuid4().hex[:8].upper()}",
            payment_date=timezone.now(),
            subscription_start=timezone.now(),
            subscription_end=subscription_end
        )
        
        # Atualizar usuário
        user = request.user
        user.plan_type = 'premium'
        user.subscription_start = timezone.now()
        user.subscription_end = subscription_end
        user.save()
        
        # Criar notificação
        Notification.objects.create(
            user=user,
            title='Assinatura Ativada',
            message=f'Assinatura {plan.name} ativada com sucesso! Válida até {subscription_end.strftime("%d/%m/%Y")}',
            notification_type='success'
        )
        
        # Criar log de auditoria
        AuditLog.objects.create(
            user=user,
            action='payment',
            model_name='Payment',
            object_id=str(payment.id),
            details=f'Pagamento realizado: {plan.name} - {plan.price}€',
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        return Response(
            PaymentSerializer(payment).data,
            status=status.HTTP_201_CREATED
        )

# ==================== DASHBOARD & UTILITY VIEWS ====================

class DashboardView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        today = timezone.now().date()
        
        # Estatísticas
        stats = {
            'user': UserSerializer(user).data,
            'appointments': {
                'total': Appointment.objects.filter(user=user).count(),
                'active': Appointment.objects.filter(
                    user=user,
                    status__in=['pending', 'confirmed']
                ).count(),
                'upcoming': Appointment.objects.filter(
                    user=user,
                    status__in=['pending', 'confirmed'],
                    scheduled_date__gte=timezone.now()
                ).order_by('scheduled_date')[:5]
            },
            'chat': {
                'sessions': ChatSession.objects.filter(user=user).count(),
                'active_sessions': ChatSession.objects.filter(user=user, is_active=True).count(),
                'today_messages': ChatMessage.objects.filter(
                    session__user=user,
                    sender_type='user',
                    created_at__date=today
                ).count()
            },
            'education': {
                'enrolled_courses': UserProgress.objects.filter(user=user).count(),
                'completed_courses': UserProgress.objects.filter(user=user, completed=True).count(),
                'progress': UserProgress.objects.filter(user=user).aggregate(
                    avg_progress=models.Avg('progress_percentage')
                )['avg_progress'] or 0
            },
            'documents': {
                'generated': GeneratedDocument.objects.filter(user=user).count(),
                'recent': GeneratedDocument.objects.filter(user=user).order_by('-created_at')[:5]
            },
            'notifications': {
                'unread': Notification.objects.filter(user=user, is_read=False).count(),
                'recent': Notification.objects.filter(user=user).order_by('-created_at')[:5]
            }
        }
        
        return Response(stats)

class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return Response({'message': 'Todas as notificações marcadas como lidas'})
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        return Response({'message': 'Notificação marcada como lida'})

# ==================== PUBLIC VIEWS ====================

@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    return Response({
        'status': 'online',
        'service': 'Juridicando API',
        'version': '1.0.0',
        'timestamp': timezone.now().isoformat()
    })

@api_view(['GET'])
@permission_classes([AllowAny])
def public_stats(request):
    stats = {
        'total_users': User.objects.filter(is_active=True).count(),
        'total_lawyers': LawyerProfile.objects.filter(is_verified=True).count(),
        'total_courses': Course.objects.filter(is_active=True).count(),
        'total_documents': DocumentTemplate.objects.filter(is_active=True).count(),
        'appointments_today': Appointment.objects.filter(
            scheduled_date__date=timezone.now().date()
        ).count(),
        'chat_sessions_today': ChatSession.objects.filter(
            created_at__date=timezone.now().date()
        ).count()
    }
    return Response(stats)

# ==================== ADMIN VIEWS ====================

class AdminDashboardView(APIView):
    permission_classes = [IsAdminUser]
    
    def get(self, request):
        # Estatísticas administrativas
        stats = {
            'users': {
                'total': User.objects.count(),
                'active': User.objects.filter(is_active=True).count(),
                'premium': User.objects.filter(plan_type='premium').count(),
                'lawyers': User.objects.filter(is_lawyer=True).count(),
                'new_today': User.objects.filter(date_joined__date=timezone.now().date()).count()
            },
            'revenue': {
                'today': Payment.objects.filter(
                    payment_date__date=timezone.now().date(),
                    status='completed'
                ).aggregate(total=models.Sum('amount'))['total'] or 0,
                'month': Payment.objects.filter(
                    payment_date__month=timezone.now().month,
                    payment_date__year=timezone.now().year,
                    status='completed'
                ).aggregate(total=models.Sum('amount'))['total'] or 0,
                'total': Payment.objects.filter(status='completed').aggregate(
                    total=models.Sum('amount')
                )['total'] or 0
            },
            'activity': {
                'appointments': Appointment.objects.count(),
                'chat_sessions': ChatSession.objects.count(),
                'documents_generated': GeneratedDocument.objects.count(),
                'course_enrollments': UserProgress.objects.count()
            },
            'recent_activity': AuditLog.objects.all().order_by('-created_at')[:10]
        }
        
        return Response(stats)