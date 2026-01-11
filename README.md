# PhotoVault - Secure AI-Powered Photo Management Platform

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Django](https://img.shields.io/badge/Django-5.2+-green.svg)](https://www.djangoproject.com/)
[![Next.js](https://img.shields.io/badge/Next.js-14+-black.svg)](https://nextjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-blue.svg)](https://www.typescriptlang.org/)

PhotoVault is a secure, AI-powered photo management platform that helps users organize, share, and discover their memories with enterprise-grade security and intelligent automation.

## 🚀 Quick Start

### One-Click Setup

**Windows:**
```bash
./setup_windows.bat
```

**Linux/Mac:**
```bash
chmod +x setup_unix.sh
./setup_unix.sh
```

**Start Demo:**
```bash
./start_demo.bat
```

### Manual Setup

1. **Clone the repository**
```bash
git clone https://github.com/abdulrehmanabdul0303-dotcom/selfie-connectfinal.git
cd selfie-connectfinal
```

2. **Backend Setup**
```bash
cd photovault_django
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
```

3. **Frontend Setup**
```bash
cd photovault-frontend
npm install
```

4. **Start Services**
```bash
# Terminal 1: Backend
cd photovault_django
python manage.py runserver 0.0.0.0:8000

# Terminal 2: Frontend  
cd photovault-frontend
npm run dev
```

## 🌟 Features

### 🔒 **Enterprise-Grade Security**
- End-to-end encryption with zero-knowledge architecture
- User-specific data encryption keys (DEK)
- Secure sharing with time-limited, password-protected links
- Complete audit trails and access logging

### 🤖 **AI-Powered Organization**
- Automatic face recognition and person clustering
- Smart album creation by events, locations, and people
- Intelligent search using natural language
- Memory timeline for rediscovering forgotten photos

### 🌐 **Professional Sharing**
- Client delivery mode for photographers
- QR code sharing for instant event access
- Collaborative albums with multi-user contributions
- Download tracking and analytics

### 📱 **Modern Experience**
- Responsive design for all devices
- Real-time synchronization
- Bulk operations for efficiency
- Offline support capabilities

## 🏗️ Architecture

### Backend (Django REST Framework)
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

### Frontend (Next.js 14)
```
photovault-frontend/
├── src/
│   ├── app/            # Next.js app router
│   ├── components/     # Reusable UI components
│   ├── lib/            # API clients, utilities
│   └── types/          # TypeScript definitions
├── public/             # Static assets
└── package.json
```

## 🔐 Security Features

- **Zero-Knowledge Encryption**: Photos encrypted before upload
- **JWT Authentication**: Secure token-based authentication
- **Rate Limiting**: Protection against abuse
- **CORS Configuration**: Secure cross-origin requests
- **Input Validation**: SQL injection and XSS protection
- **Audit Logging**: Complete activity tracking

## 📊 API Endpoints

### Authentication
```
POST /api/auth/register/     # User registration
POST /api/auth/login/        # User login
POST /api/auth/logout/       # User logout
GET  /api/auth/me/           # Get current user
POST /api/auth/verify/       # Email verification
```

### Images
```
GET    /api/images/          # List user images
POST   /api/images/upload/   # Upload new image
GET    /api/images/{id}/     # Get image details
DELETE /api/images/{id}/     # Delete image
GET    /api/images/search/   # Search images
```

### Albums
```
GET    /api/albums/          # List user albums
POST   /api/albums/          # Create new album
GET    /api/albums/{id}/     # Get album details
PUT    /api/albums/{id}/     # Update album
DELETE /api/albums/{id}/     # Delete album
```

### Sharing
```
POST   /api/sharing/         # Create share link
GET    /api/sharing/{token}/ # Access shared content
DELETE /api/sharing/{id}/    # Revoke share link
```

## 🎯 Demo Accounts

After running the setup, you can use these demo accounts:

- **Admin**: `admin@photovault.com` / `admin123`
- **Photographer**: `photographer@demo.com` / `demo123`
- **Family User**: `family@demo.com` / `demo123`
- **Business User**: `business@demo.com` / `demo123`

## 🛠️ Development

### Prerequisites
- Python 3.8+
- Node.js 16+
- Git

### Environment Variables

**Backend (.env):**
```bash
DEBUG=True
SECRET_KEY=your-secret-key
DATABASE_URL=sqlite:///db.sqlite3
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0
CORS_ALLOWED_ORIGINS=http://localhost:3000
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

**Frontend (.env.local):**
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_APP_NAME=PhotoVault
```

### Testing
```bash
# Backend tests
cd photovault_django
python manage.py test

# Frontend tests
cd photovault-frontend
npm test
```

### Code Quality
```bash
# Backend
flake8 .
black .
isort .

# Frontend
npm run lint
npm run format
```

## 🚀 Deployment

### Docker
```bash
docker-compose up --build
```

### Production Checklist
- [ ] Set `DEBUG=False`
- [ ] Configure production database (PostgreSQL)
- [ ] Set up Redis for caching
- [ ] Configure email backend (SMTP)
- [ ] Set up file storage (AWS S3/CloudFlare R2)
- [ ] Configure HTTPS
- [ ] Set up monitoring and logging

## 📚 Documentation

- [Developer Guide](DEVELOPER_GUIDE.md) - Complete technical documentation
- [Marketing Guide](MARKETING_GUIDE.md) - Product positioning and demos
- [Quick Start Scripts](QUICK_START_SCRIPTS.md) - Essential commands and references

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Code Style
- Follow PEP 8 for Python
- Use ESLint/Prettier for JavaScript/TypeScript
- Write descriptive commit messages
- Add tests for new features

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Django REST Framework for the robust backend API
- Next.js for the modern frontend framework
- TailwindCSS for beautiful, responsive design
- All contributors who helped make this project possible

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/abdulrehmanabdul0303-dotcom/selfie-connectfinal/issues)
- **Discussions**: [GitHub Discussions](https://github.com/abdulrehmanabdul0303-dotcom/selfie-connectfinal/discussions)
- **Email**: support@photovault.com

## 🌟 Star History

[![Star History Chart](https://api.star-history.com/svg?repos=abdulrehmanabdul0303-dotcom/selfie-connectfinal&type=Date)](https://star-history.com/#abdulrehmanabdul0303-dotcom/selfie-connectfinal&Date)

---

**Made with ❤️ by the PhotoVault Team**