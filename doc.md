# 📚 Documentação da API Juridicando

## 🌟 Visão Geral
A API Juridicando é uma plataforma digital de acesso à justiça que oferece serviços jurídicos através de tecnologia. A API segue arquitetura REST e utiliza autenticação por token.

**URL Base:** `http://localhost:8000/api/`

**Formato de Resposta:** JSON

## 🔐 Autenticação

### 📝 Registro de Usuário
**POST** `/api/auth/register/`

**Body:**
```json
{
  "email": "usuario@exemplo.com",
  "full_name": "Nome Completo",
  "phone": "+351912345678",
  "password": "senha123",
  "password2": "senha123"
}
```

**Resposta (201):**
```json
{
  "token": "token_de_autenticacao",
  "user": {
    "id": "uuid",
    "email": "usuario@exemplo.com",
    "full_name": "Nome Completo",
    "plan_type": "free",
    "is_premium": false
  }
}
```

### 🔑 Login
**POST** `/api/auth/login/`

**Body:**
```json
{
  "email": "usuario@exemplo.com",
  "password": "senha123"
}
```

**Resposta (200):**
```json
{
  "token": "token_de_autenticacao",
  "user": {
    "id": "uuid",
    "email": "usuario@exemplo.com",
    "full_name": "Nome Completo",
    "plan_type": "premium",
    "is_premium": true
  }
}
```

### 👤 Usuário Atual
**GET** `/api/auth/me/`

**Headers:**
```
Authorization: Token token_de_autenticacao
```

**Resposta (200):**
```json
{
  "id": "uuid",
  "email": "usuario@exemplo.com",
  "full_name": "Nome Completo",
  "plan_type": "premium",
  "is_premium": true,
  "profile": {
    "bio": "Descrição do usuário",
    "phone": "+351912345678",
    "address": "Endereço",
    "city": "Cidade",
    "country": "Portugal"
  }
}
```

### 🚪 Logout
**POST** `/api/auth/logout/`

**Headers:**
```
Authorization: Token token_de_autenticacao
```

**Resposta (200):**
```json
{
  "message": "Logout realizado com sucesso!"
}
```

## 🤖 Chatbot Jurídico

### 📚 Tópicos Legais
**GET** `/api/legal-topics/`

**Resposta (200):**
```json
[
  {
    "id": "uuid",
    "name": "Direito Civil",
    "description": "Contratos, propriedade, obrigações",
    "category": "Civil",
    "keywords": ["contrato", "propriedade", "danos"]
  }
]
```

### 💬 Sessões de Chat
**GET** `/api/chat-sessions/` - Listar sessões
**POST** `/api/chat-sessions/` - Criar nova sessão

**Body (POST):**
```json
{
  "title": "Minha questão sobre contratos",
  "topic": "uuid_do_topico"
}
```

### 📨 Enviar Mensagem
**POST** `/api/chat-sessions/{id}/send_message/`

**Body:**
```json
{
  "content": "Qual a validade de um contrato verbal?"
}
```

**Resposta (200):**
```json
{
  "user_message": {
    "id": "uuid",
    "sender_type": "user",
    "content": "Qual a validade de um contrato verbal?",
    "created_at": "2024-01-15T10:30:00Z"
  },
  "ai_response": {
    "id": "uuid",
    "sender_type": "assistant",
    "content": "Baseado no Código Civil português...",
    "legal_references": [
      {
        "code": "Código Civil",
        "article": "405º",
        "title": "Definição de contrato"
      }
    ],
    "created_at": "2024-01-15T10:30:05Z"
  }
}
```

### 📋 Mensagens de uma Sessão
**GET** `/api/chat-sessions/{id}/messages/`

## ⚖️ Agendamentos com Advogados

### 👨‍⚖️ Listar Advogados
**GET** `/api/lawyers/`

**Parâmetros de Query:**
- `search`: Busca por nome, especialização
- `ordering`: rating, hourly_rate, experience_years
- `specializations`: Filtro por especialização

**Resposta (200):**
```json
[
  {
    "id": "uuid",
    "user": {
      "full_name": "Dr. João Silva",
      "email": "advogado@exemplo.com"
    },
    "specializations": ["Direito Civil", "Contratos"],
    "experience_years": 10,
    "hourly_rate": 100.00,
    "rating": 4.8,
    "is_verified": true,
    "is_available": true
  }
]
```

### 📅 Verificar Disponibilidade
**GET** `/api/lawyers/{id}/availability/?date=2024-01-20`

**Resposta (200):**
```json
{
  "lawyer": "Dr. João Silva",
  "date": "2024-01-20",
  "available_slots": [
    {"start_time": "09:00", "end_time": "09:30"},
    {"start_time": "09:30", "end_time": "10:00"}
  ]
}
```

### 📝 Agendar Consulta
**POST** `/api/appointments/`

**Body:**
```json
{
  "lawyer": "uuid_do_advogado",
  "scheduled_date": "2024-01-20T09:00:00Z",
  "duration": 60,
  "consultation_type": "online",
  "notes": "Questão sobre contrato de trabalho",
  "location": "Endereço (se presencial)"
}
```

### ✅ Confirmar Consulta (Advogado)
**POST** `/api/appointments/{id}/confirm/`

### ❌ Cancelar Consulta
**POST** `/api/appointments/{id}/cancel/`

## 📚 Plataforma Educacional

### 🗂️ Categorias de Cursos
**GET** `/api/course-categories/`

### 📖 Listar Cursos
**GET** `/api/courses/`

**Parâmetros de Query:**
- `search`: Busca por título, descrição
- `category`: Filtro por categoria
- `difficulty`: beginner, intermediate, advanced
- `is_premium`: true/false

**Resposta (200):**
```json
[
  {
    "id": "uuid",
    "title": "Introdução ao Direito Civil",
    "description": "Curso básico sobre Direito Civil",
    "category": "Direito Civil",
    "difficulty": "beginner",
    "duration_hours": 10,
    "is_premium": false,
    "price": 0.00,
    "lesson_count": 8,
    "enrolled_count": 150
  }
]
```

### 🎓 Inscrever-se em Curso
**POST** `/api/courses/{id}/enroll/`

### 📚 Lições do Curso
**GET** `/api/courses/{id}/lessons/`

### 📊 Progresso do Usuário
**GET** `/api/user-progress/`

### ✅ Completar Lição
**POST** `/api/user-progress/{id}/complete_lesson/`

**Body:**
```json
{
  "lesson_id": "uuid_da_licao"
}
```

## 📄 Geração de Documentos

### 🗂️ Categorias de Documentos
**GET** `/api/document-categories/`

### 📋 Modelos de Documentos
**GET** `/api/document-templates/`

**Resposta (200):**
```json
[
  {
    "id": "uuid",
    "name": "Contrato de Prestação de Serviços",
    "description": "Modelo padrão para contrato de serviços",
    "category": "Contratos",
    "is_premium": false,
    "price": 0.00,
    "fields_schema": {
      "partes": ["contratante", "contratado"],
      "servico": "texto",
      "valor": "numero",
      "prazo": "data"
    }
  }
]
```

### 🖨️ Gerar Documento
**POST** `/api/document-templates/{id}/generate/`

**Body:**
```json
{
  "data": {
    "contratante": "João Silva",
    "contratado": "Empresa XYZ",
    "servico": "Desenvolvimento de software",
    "valor": 5000,
    "prazo": "2024-06-30"
  }
}
```

**Resposta (201):**
```json
{
  "message": "Documento gerado com sucesso",
  "document_id": "uuid",
  "document_name": "Contrato de Prestação de Serviços"
}
```

### 📥 Download de Documento
**POST** `/api/generated-documents/{id}/download/`

## 💰 Pagamentos e Assinaturas

### 📊 Planos Disponíveis
**GET** `/api/subscription-plans/`

**Resposta (200):**
```json
[
  {
    "id": "uuid",
    "name": "Premium Mensal",
    "description": "Acesso completo por 30 dias",
    "price": 29.90,
    "period": "monthly",
    "features": [
      "Chatbot ilimitado",
      "Agendamentos ilimitados",
      "Cursos premium",
      "Modelos de documentos premium"
    ]
  }
]
```

### 💳 Realizar Pagamento
**POST** `/api/payments/`

**Body:**
```json
{
  "plan_id": "uuid_do_plano",
  "payment_method": "credit_card"
}
```

**Resposta (201):**
```json
{
  "id": "uuid",
  "user": "uuid_do_usuario",
  "plan": {
    "name": "Premium Mensal",
    "price": 29.90
  },
  "amount": 29.90,
  "status": "completed",
  "transaction_id": "TXN-ABC123",
  "subscription_end": "2024-02-15T10:30:00Z"
}
```

## 📊 Dashboard

### 🎯 Dashboard do Usuário
**GET** `/api/dashboard/`

**Headers:**
```
Authorization: Token token_de_autenticacao
```

**Resposta (200):**
```json
{
  "user": {
    "email": "usuario@exemplo.com",
    "full_name": "Nome Completo",
    "plan_type": "premium",
    "is_premium": true
  },
  "appointments": {
    "total": 5,
    "active": 2,
    "upcoming": [
      {
        "id": "uuid",
        "lawyer_name": "Dr. João Silva",
        "scheduled_date": "2024-01-20T09:00:00Z",
        "status": "confirmed"
      }
    ]
  },
  "chat": {
    "sessions": 12,
    "active_sessions": 1,
    "today_messages": 3
  },
  "education": {
    "enrolled_courses": 3,
    "completed_courses": 1,
    "progress": 65
  },
  "documents": {
    "generated": 8,
    "recent": [...]
  },
  "notifications": {
    "unread": 2,
    "recent": [...]
  }
}
```

## 🔔 Notificações

### 🔔 Listar Notificações
**GET** `/api/notifications/`

### ✅ Marcar como Lida
**POST** `/api/notifications/{id}/mark_read/`

### ✅ Marcar Todas como Lidas
**POST** `/api/notifications/mark_all_read/`

## ⚙️ Endpoints Públicos

### 🩺 Health Check
**GET** `/api/health/`

**Resposta (200):**
```json
{
  "status": "online",
  "service": "Juridicando API",
  "version": "1.0.0",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### 📈 Estatísticas Públicas
**GET** `/api/stats/`

**Resposta (200):**
```json
{
  "total_users": 1250,
  "total_lawyers": 85,
  "total_courses": 42,
  "total_documents": 28,
  "appointments_today": 15,
  "chat_sessions_today": 47
}
```

## 🔐 Permissões e Limites

### 👤 Usuário Free (Gratuito)
- ✅ Chatbot: 5 mensagens/dia
- ✅ Agendamentos: 1 ativo por vez
- ✅ Cursos: Apenas gratuitos
- ✅ Documentos: Apenas modelos gratuitos

### 👑 Usuário Premium
- ✅ Chatbot: Ilimitado
- ✅ Agendamentos: Ilimitados
- ✅ Cursos: Acesso a todos
- ✅ Documentos: Todos os modelos
- ✅ Prioridade no suporte

## 🚨 Códigos de Status HTTP

| Código | Descrição |
|--------|-----------|
| 200 | OK - Requisição bem-sucedida |
| 201 | Created - Recurso criado com sucesso |
| 400 | Bad Request - Erro na requisição |
| 401 | Unauthorized - Autenticação necessária |
| 403 | Forbidden - Permissão negada |
| 404 | Not Found - Recurso não encontrado |
| 500 | Internal Server Error - Erro no servidor |

## 📝 Exemplos de Uso

### Exemplo 1: Criar usuário e usar chatbot
```bash
# 1. Registrar
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","full_name":"João Silva","password":"senha123","password2":"senha123"}'

# 2. Login
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"senha123"}'

# 3. Usar chatbot (com token)
curl -X POST http://localhost:8000/api/chat-sessions/ \
  -H "Authorization: Token SEU_TOKEN_AQUI" \
  -H "Content-Type: application/json" \
  -d '{"title":"Minha questão legal"}'
```

### Exemplo 2: Agendar consulta
```bash
curl -X POST http://localhost:8000/api/appointments/ \
  -H "Authorization: Token SEU_TOKEN_AQUI" \
  -H "Content-Type: application/json" \
  -d '{
    "lawyer": "uuid_advogado",
    "scheduled_date": "2024-01-20T09:00:00Z",
    "consultation_type": "online",
    "notes": "Consulta sobre contrato"
  }'
```

### Exemplo 3: Gerar documento
```bash
curl -X POST http://localhost:8000/api/document-templates/uuid_template/generate/ \
  -H "Authorization: Token SEU_TOKEN_AQUI" \
  -H "Content-Type: application/json" \
  -d '{
    "data": {
      "contratante": "Maria Santos",
      "servico": "Consultoria jurídica",
      "valor": 2500,
      "prazo": "2024-03-31"
    }
  }'
```

## 🛠️ Configuração do Ambiente

### Variáveis de Ambiente (`.env`)
```env
DEBUG=True
SECRET_KEY=sua_chave_secreta
DATABASE_URL=sqlite:///db.sqlite3
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOW_ALL_ORIGINS=True
```

### Instalação
```bash
# 1. Clonar repositório
git clone [repositorio]
cd juridicando_project

# 2. Criar ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# 3. Instalar dependências
pip install -r requirements.txt

# 4. Configurar banco de dados
python manage.py migrate

# 5. Criar superusuário
python manage.py createsuperuser

# 6. Iniciar servidor
python manage.py runserver
```

## 📱 Integração com Frontend

### Headers Obrigatórios
```javascript
const headers = {
  'Content-Type': 'application/json',
  'Authorization': `Token ${token}`
};
```

### Exemplo JavaScript (Fetch API)
```javascript
async function login(email, password) {
  const response = await fetch('http://localhost:8000/api/auth/login/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ email, password })
  });
  
  const data = await response.json();
  localStorage.setItem('token', data.token);
  return data.user;
}

async function getDashboard() {
  const token = localStorage.getItem('token');
  const response = await fetch('http://localhost:8000/api/dashboard/', {
    headers: {
      'Authorization': `Token ${token}`
    }
  });
  
  return await response.json();
}
```

## 🔍 Testes

### Testar Endpoints
```bash
# Testar health check
curl http://localhost:8000/api/health/

# Testar autenticação
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"admin123"}'
```

## 🐛 Troubleshooting

### Problemas Comuns:

1. **Erro 401 Unauthorized**
   - Verificar se o token está correto
   - Token pode ter expirado (fazer login novamente)

2. **Erro 403 Forbidden**
   - Usuário não tem permissão para o recurso
   - Limite do plano free atingido

3. **Erro 404 Not Found**
   - Verificar URL do endpoint
   - Recurso pode ter sido removido

4. **Erro 400 Bad Request**
   - Verificar formato do JSON
   - Campos obrigatórios faltando

### Logs do Servidor:
```bash
# Ver logs do Django
python manage.py runserver --verbosity 2

# Ver banco de dados
python manage.py dbshell
```

## 📞 Suporte

- **Documentação:** `/api/docs/` (em desenvolvimento)
- **Issues:** Repositório do projeto
- **Email:** suporte@juridicando.com

---

**Versão:** 1.0.0  
**Última Atualização:** 15/01/2024  
**Equipe:** benyaminne Weya, Luciano Alfredo, Mário da Silva