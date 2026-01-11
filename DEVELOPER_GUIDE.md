# PhotoVault Developer Guide

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+
- Git

### 1. Clone & Setup
```bash
# Clone the repository
git clone <repository-url>
cd photovault

# Backend setup
cd photovault_django
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac
pip install -r requirements.txt

# Frontend setup
cd ../photovault-frontend
npm install
```

### 2. Environment Configuration
```bash
# Backend (.env)
cd photovault_django
cp .env.example .env
# Edit .env with your settings
```

### 3. Database Setup
```bash
# Run migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
```

### 4. Start Development Servers
```bash
# Terminal 1: Backend
cd photovault_django
python manage.py runserver 0.0.0.0:8000

# Terminal 2: Frontend
cd photovault-frontend
npm run dev
```

## 🏗️ Architecture Overview

### Backend (Django)
```
photovault_django/
├── apps/
│   ├── users/          # Authentication & user management
│   ├── images/         # Image upload, storage, metadata
│   ├── albums/         # Album creation & management
│   ├── sharing/        # Share links & permissions
│   ├── memories/       # AI-powered memories & events
│   ├── audit/          # Security logging
│   └── core/           # Common utilities
├── photovault/         # Django settings
└── manage.py
```

### Frontend (Next.js)
```
photovault-frontend/
├── src/
│   ├── app/            # Next.js 13+ app router
│   ├── components/     # Reusable UI components
│   ├── lib/            # API clients, utilities
│   └── types/          # TypeScript definitions
├── public/             # Static assets
└── package.json
```

## 🔧 Development Workflow

### API Development
1. **Create Models** in `apps/{app}/models.py`
2. **Create Serializers** in `apps/{app}/serializers.py`
3. **Create Views** in `apps/{app}/views.py`
4. **Add URLs** in `apps/{app}/urls.py`
5. **Run Migrations** `python manage.py makemigrations && python manage.py migrate`

### Frontend Development
1. **Create Components** in `src/components/`
2. **Add API Calls** in `src/lib/api/`
3. **Create Pages** in `src/app/`
4. **Add Types** in `src/lib/types/`

## 🧪 Testing

### Backend Tests
```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test apps.users

# Run with coverage
coverage run --source='.' manage.py test
coverage report
```

### Frontend Tests
```bash
# Run tests
npm test

# Run with coverage
npm run test:coverage
```

## 🔐 Security Features

### Authentication
- JWT-based authentication
- Email verification required
- Password reset functionality
- Account lockout after failed attempts

### Data Protection
- End-to-end encryption for sensitive data
- User-specific data encryption keys (DEK)
- Secure file storage with access controls
- Audit logging for all actions

### API Security
- Rate limiting on all endpoints
- CORS configuration
- Input validation and sanitization
- SQL injection protection

## 📊 Database Schema

### Key Models
```python
# User Model
class User(AbstractUser):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=255)
    email_verified = models.BooleanField(default=False)
    dek_encrypted_b64 = models.TextField()  # Encrypted data key

# Image Model
class Image(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    original_filename = models.CharField(max_length=255)
    storage_key = models.CharField(max_length=255, unique=True)
    file_size = models.BigIntegerField()
    mime_type = models.CharField(max_length=100)
    
# Album Model
class Album(models.Model):
    name = models.CharField(max_length=255)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    images = models.ManyToManyField(Image, through='AlbumImage')
```

## 🚀 Deployment

### Production Checklist
- [ ] Set `DEBUG=False`
- [ ] Configure production database (PostgreSQL)
- [ ] Set up Redis for caching
- [ ] Configure email backend
- [ ] Set up file storage (AWS S3/CloudFlare R2)
- [ ] Configure HTTPS
- [ ] Set up monitoring and logging

### Docker Deployment
```bash
# Build and run with Docker Compose
docker-compose up --build
```

## 🔍 Debugging

### Common Issues
1. **CORS Errors**: Check `CORS_ALLOWED_ORIGINS` in `.env`
2. **Database Errors**: Run `python manage.py migrate`
3. **Authentication Issues**: Verify JWT settings
4. **File Upload Issues**: Check storage configuration

### Logging
```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📚 API Documentation

### Authentication Endpoints
```
POST /api/auth/register/     # User registration
POST /api/auth/login/        # User login
POST /api/auth/logout/       # User logout
GET  /api/auth/me/           # Get current user
```

### Image Endpoints
```
GET    /api/images/          # List user images
POST   /api/images/upload/   # Upload new image
GET    /api/images/{id}/     # Get image details
DELETE /api/images/{id}/     # Delete image
```

### Album Endpoints
```
GET    /api/albums/          # List user albums
POST   /api/albums/          # Create new album
GET    /api/albums/{id}/     # Get album details
PUT    /api/albums/{id}/     # Update album
DELETE /api/albums/{id}/     # Delete album
```

## 🛠️ Useful Commands

### Django Management Commands
```bash
# Create sample data
python manage.py shell -c "exec(open('create_sample_data.py').read())"

# Clear cache
python manage.py shell -c "from django.core.cache import cache; cache.clear()"

# Check for issues
python manage.py check

# Collect static files
python manage.py collectstatic
```

### Database Commands
```bash
# Reset database
python manage.py flush

# Backup database
python manage.py dumpdata > backup.json

# Restore database
python manage.py loaddata backup.json
```

## 🔧 Configuration

### Environment Variables
```bash
# Required
SECRET_KEY=your-secret-key
DATABASE_URL=sqlite:///db.sqlite3
DEBUG=True

# Optional
REDIS_URL=redis://localhost:6379/0
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
CORS_ALLOWED_ORIGINS=http://localhost:3000
```

## 📈 Performance Optimization

### Database Optimization
- Use `select_related()` and `prefetch_related()`
- Add database indexes for frequently queried fields
- Use database connection pooling

### Caching
- Redis for session storage
- Cache API responses
- Use CDN for static files

### Frontend Optimization
- Image lazy loading
- Code splitting
- Bundle optimization
- Service worker for offline support

## 🤝 Contributing

### Code Style
- Follow PEP 8 for Python
- Use ESLint/Prettier for JavaScript/TypeScript
- Write descriptive commit messages
- Add tests for new features

### Pull Request Process
1. Fork the repository
2. Create feature branch
3. Write tests
4. Update documentation
5. Submit pull request

## 📞 Support

### Getting Help
- Check the documentation
- Search existing issues
- Create detailed bug reports
- Join the developer community

### Useful Resources
- Django Documentation: https://docs.djangoproject.com/
- Next.js Documentation: https://nextjs.org/docs
- Django REST Framework: https://www.django-rest-framework.org/