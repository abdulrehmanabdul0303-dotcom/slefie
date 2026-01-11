# PhotoVault Quick Start Scripts

## 🚀 One-Click Setup Scripts

### Windows Setup Script
Create `setup_windows.bat`:

```batch
@echo off
echo ========================================
echo PhotoVault Quick Setup for Windows
echo ========================================

echo.
echo [1/6] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.8+ from python.org
    pause
    exit /b 1
)

echo [2/6] Checking Node.js installation...
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js not found. Please install Node.js 16+ from nodejs.org
    pause
    exit /b 1
)

echo [3/6] Setting up Python virtual environment...
cd photovault_django
python -m venv .venv
call .venv\Scripts\activate.bat
pip install -r requirements.txt

echo [4/6] Setting up database...
python manage.py makemigrations
python manage.py migrate

echo [5/6] Creating admin user...
echo Creating admin user (admin@photovault.com / admin123)
python manage.py shell -c "from apps.users.models import User; User.objects.create_superuser('admin@photovault.com', 'admin123', name='Admin User', email_verified=True) if not User.objects.filter(email='admin@photovault.com').exists() else print('Admin user already exists')"

echo [6/6] Setting up frontend...
cd ..\photovault-frontend
npm install

echo.
echo ========================================
echo Setup Complete! 
echo ========================================
echo.
echo To start the application:
echo 1. Backend:  cd photovault_django ^&^& .venv\Scripts\activate ^&^& python manage.py runserver 0.0.0.0:8000
echo 2. Frontend: cd photovault-frontend ^&^& npm run dev
echo.
echo Login credentials:
echo Email: admin@photovault.com
echo Password: admin123
echo.
echo Backend URL: http://localhost:8000
echo Frontend URL: http://localhost:3000
echo.
pause
```

### Linux/Mac Setup Script
Create `setup_unix.sh`:

```bash
#!/bin/bash

echo "========================================"
echo "PhotoVault Quick Setup for Linux/Mac"
echo "========================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python
echo -e "\n${YELLOW}[1/6] Checking Python installation...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}ERROR: Python 3 not found. Please install Python 3.8+${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Python found: $(python3 --version)${NC}"

# Check Node.js
echo -e "\n${YELLOW}[2/6] Checking Node.js installation...${NC}"
if ! command -v node &> /dev/null; then
    echo -e "${RED}ERROR: Node.js not found. Please install Node.js 16+${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Node.js found: $(node --version)${NC}"

# Setup Python environment
echo -e "\n${YELLOW}[3/6] Setting up Python virtual environment...${NC}"
cd photovault_django
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
echo -e "${GREEN}✓ Python environment ready${NC}"

# Setup database
echo -e "\n${YELLOW}[4/6] Setting up database...${NC}"
python manage.py makemigrations
python manage.py migrate
echo -e "${GREEN}✓ Database ready${NC}"

# Create admin user
echo -e "\n${YELLOW}[5/6] Creating admin user...${NC}"
python manage.py shell -c "
from apps.users.models import User
if not User.objects.filter(email='admin@photovault.com').exists():
    User.objects.create_superuser('admin@photovault.com', 'admin123', name='Admin User', email_verified=True)
    print('Admin user created')
else:
    print('Admin user already exists')
"
echo -e "${GREEN}✓ Admin user ready${NC}"

# Setup frontend
echo -e "\n${YELLOW}[6/6] Setting up frontend...${NC}"
cd ../photovault-frontend
npm install
echo -e "${GREEN}✓ Frontend ready${NC}"

echo -e "\n${GREEN}========================================"
echo "Setup Complete! 🎉"
echo "========================================${NC}"
echo -e "\nTo start the application:"
echo -e "${YELLOW}1. Backend:${NC}  cd photovault_django && source .venv/bin/activate && python manage.py runserver 0.0.0.0:8000"
echo -e "${YELLOW}2. Frontend:${NC} cd photovault-frontend && npm run dev"
echo -e "\n${YELLOW}Login credentials:${NC}"
echo "Email: admin@photovault.com"
echo "Password: admin123"
echo -e "\n${YELLOW}URLs:${NC}"
echo "Backend:  http://localhost:8000"
echo "Frontend: http://localhost:3000"
```

## 🎬 Demo Data Script

### Create Sample Data Script
Create `create_demo_data.py`:

```python
#!/usr/bin/env python
"""
PhotoVault Demo Data Generator
Creates sample users, albums, and images for demonstration purposes.
"""

import os
import sys
import django
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'photovault.settings')
django.setup()

from apps.users.models import User
from apps.albums.models import Album
from apps.images.models import Image, Folder
from django.utils import timezone
from datetime import timedelta
import random

def create_demo_users():
    """Create demo users for different personas."""
    users = [
        {
            'email': 'photographer@demo.com',
            'name': 'Sarah Johnson',
            'password': 'demo123',
            'role': 'Professional Photographer'
        },
        {
            'email': 'family@demo.com', 
            'name': 'Mike Chen',
            'password': 'demo123',
            'role': 'Family User'
        },
        {
            'email': 'business@demo.com',
            'name': 'Emma Rodriguez', 
            'password': 'demo123',
            'role': 'Business User'
        }
    ]
    
    created_users = []
    for user_data in users:
        user, created = User.objects.get_or_create(
            email=user_data['email'],
            defaults={
                'name': user_data['name'],
                'email_verified': True,
                'is_active': True
            }
        )
        if created:
            user.set_password(user_data['password'])
            user.save()
            print(f"✓ Created user: {user.name} ({user.email})")
        else:
            print(f"• User already exists: {user.name}")
        created_users.append(user)
    
    return created_users

def create_demo_folders(user):
    """Create sample folders for organization."""
    folders = [
        'Wedding Photography',
        'Family Portraits', 
        'Corporate Events',
        'Travel Photos',
        'Product Shots'
    ]
    
    created_folders = []
    for folder_name in folders:
        folder, created = Folder.objects.get_or_create(
            name=folder_name,
            user=user,
            defaults={'description': f'Sample {folder_name.lower()} folder'}
        )
        if created:
            print(f"  ✓ Created folder: {folder_name}")
        created_folders.append(folder)
    
    return created_folders

def create_demo_albums(user):
    """Create sample albums with different themes."""
    albums_data = [
        {
            'name': 'Johnson Wedding 2024',
            'description': 'Beautiful wedding ceremony and reception photos',
            'album_type': 'event'
        },
        {
            'name': 'Family Vacation - Hawaii',
            'description': 'Amazing family trip to Hawaii with stunning beaches',
            'album_type': 'personal'
        },
        {
            'name': 'Corporate Retreat 2024',
            'description': 'Team building and networking event photos',
            'album_type': 'business'
        },
        {
            'name': 'Product Launch Event',
            'description': 'New product unveiling and media coverage',
            'album_type': 'business'
        },
        {
            'name': 'Kids Birthday Party',
            'description': 'Memorable moments from the birthday celebration',
            'album_type': 'personal'
        }
    ]
    
    created_albums = []
    for album_data in albums_data:
        album, created = Album.objects.get_or_create(
            name=album_data['name'],
            owner=user,
            defaults={
                'description': album_data['description'],
                'created_at': timezone.now() - timedelta(days=random.randint(1, 90))
            }
        )
        if created:
            print(f"  ✓ Created album: {album.name}")
        created_albums.append(album)
    
    return created_albums

def create_sample_images(user, folders, albums):
    """Create sample image records (without actual files)."""
    sample_images = [
        {
            'filename': 'wedding_ceremony_001.jpg',
            'description': 'Bride walking down the aisle',
            'folder': folders[0] if folders else None,
            'album': albums[0] if albums else None
        },
        {
            'filename': 'wedding_reception_045.jpg', 
            'description': 'First dance moment',
            'folder': folders[0] if folders else None,
            'album': albums[0] if albums else None
        },
        {
            'filename': 'hawaii_beach_sunset.jpg',
            'description': 'Beautiful sunset at Waikiki Beach',
            'folder': folders[3] if folders else None,
            'album': albums[1] if albums else None
        },
        {
            'filename': 'family_group_photo.jpg',
            'description': 'Whole family together on the beach',
            'folder': folders[1] if folders else None,
            'album': albums[1] if albums else None
        },
        {
            'filename': 'corporate_team_building.jpg',
            'description': 'Team working together on challenges',
            'folder': folders[2] if folders else None,
            'album': albums[2] if albums else None
        }
    ]
    
    created_images = []
    for img_data in sample_images:
        # Create a unique storage key
        storage_key = f"demo/{user.id}/{img_data['filename']}"
        
        image, created = Image.objects.get_or_create(
            storage_key=storage_key,
            defaults={
                'user': user,
                'original_filename': img_data['filename'],
                'file_size': random.randint(1000000, 5000000),  # 1-5MB
                'mime_type': 'image/jpeg',
                'folder': img_data['folder'],
                'created_at': timezone.now() - timedelta(days=random.randint(1, 30))
            }
        )
        
        if created:
            print(f"    ✓ Created image: {img_data['filename']}")
            # Add to album if specified
            if img_data['album']:
                img_data['album'].images.add(image)
        
        created_images.append(image)
    
    return created_images

def main():
    """Main demo data creation function."""
    print("🎬 Creating PhotoVault Demo Data...")
    print("=" * 50)
    
    # Create demo users
    print("\n👥 Creating demo users...")
    users = create_demo_users()
    
    # Create demo data for each user
    for user in users:
        print(f"\n📁 Creating demo data for {user.name}...")
        
        # Create folders
        folders = create_demo_folders(user)
        
        # Create albums  
        albums = create_demo_albums(user)
        
        # Create sample images
        images = create_sample_images(user, folders, albums)
    
    print("\n" + "=" * 50)
    print("🎉 Demo data creation complete!")
    print("\nDemo Users Created:")
    print("• photographer@demo.com / demo123 (Professional Photographer)")
    print("• family@demo.com / demo123 (Family User)")  
    print("• business@demo.com / demo123 (Business User)")
    print("\nYou can now login with any of these accounts to see sample data.")

if __name__ == '__main__':
    main()
```

## 🎯 Marketing Demo Script

### 5-Minute Marketing Demo
Create `marketing_demo_script.md`:

```markdown
# PhotoVault 5-Minute Marketing Demo Script

## Pre-Demo Setup (2 minutes before)
1. Open PhotoVault in browser (http://localhost:3000)
2. Have demo data loaded
3. Prepare sample photos for upload demo
4. Clear browser cache for fresh experience

## Demo Flow (5 minutes)

### Opening Hook (30 seconds)
**"Let me show you how PhotoVault solves the three biggest problems with photo management in just 5 minutes."**

*[Screen: PhotoVault login page]*

**"First, let me log in as Sarah, a professional wedding photographer."**

*[Login with photographer@demo.com / demo123]*

### Problem 1: Organization Chaos (90 seconds)

**"Problem one: Photo chaos. Sarah just shot a 300-photo wedding. Watch what happens when she uploads them."**

*[Navigate to upload page, select sample wedding photos]*

**"As the photos upload, PhotoVault's AI is working in real-time:"**
- *[Point to progress indicators]*
- **"It's detecting faces and grouping people"**
- **"Identifying the venue and event type"** 
- **"Understanding the timeline of events"**

*[Navigate to albums page]*

**"Within minutes, Sarah has smart albums automatically created:"**
- *[Show auto-generated albums: Ceremony, Reception, Family Photos]*
- **"No manual sorting. No tagging. Just intelligent organization."**

*[Click on "Ceremony" album]*

**"And look at this - every photo of the bride, automatically grouped. Sarah can find any photo in seconds, not hours."**

### Problem 2: Security Concerns (90 seconds)

**"Problem two: Security. Most platforms can see your photos. PhotoVault is different."**

*[Navigate to security settings or show encryption indicator]*

**"Every photo is encrypted on Sarah's device before upload. We use zero-knowledge encryption - even if someone hacked our servers, they'd only find encrypted data."**

*[Navigate to sharing section]*

**"For client delivery, Sarah creates secure share links:"**
- *[Create new share link]*
- **"Password protected"**
- **"Expiration dates"** 
- **"Download tracking"**
- **"Watermark protection"**

*[Show share link preview]*

**"The couple gets a beautiful, branded gallery. Sarah can see exactly who viewed what photos and when. Perfect for professional client delivery."**

### Problem 3: Sharing Complexity (90 seconds)

**"Problem three: Sharing complexity. Traditional methods are either insecure or complicated."**

*[Show client gallery view]*

**"PhotoVault makes secure sharing simple. The couple can:"**
- **"View photos in a beautiful gallery"**
- **"Download high-resolution versions"**
- **"Share favorites with family"**
- **"Leave comments and feedback"**

*[Show QR code feature]*

**"For events, we have QR code sharing. Guests scan and instantly access photos on their phones. No apps to download, no accounts to create."**

*[Navigate to analytics dashboard]*

**"Sarah gets complete analytics:"**
- **"Who accessed the gallery"**
- **"Which photos were downloaded"**
- **"Client engagement metrics"**

### Advanced Features Highlight (60 seconds)

**"PhotoVault also includes advanced features:"**

*[Show memory timeline]*
- **"Memory timelines that surface forgotten photos"**

*[Show collaborative albums]*
- **"Collaborative albums where multiple people contribute"**

*[Show audit logs]*
- **"Complete audit trails for compliance"**

*[Show mobile responsive view]*
- **"Works perfectly on any device"**

### Closing (30 seconds)

**"PhotoVault combines three things that have never been combined before:"**
1. **"The intelligence of modern AI"**
2. **"The security of enterprise software"** 
3. **"The simplicity of consumer apps"**

**"Whether you're a photographer delivering to clients, a family preserving memories, or a business managing corporate photos, PhotoVault transforms photo management from a chore into a joy."**

*[Show pricing page]*

**"Starting at just $9.99 per month, with a free tier to get started. Any questions?"**

## Demo Tips

### Technical Preparation
- Ensure fast internet connection
- Use incognito/private browsing mode
- Have backup demo environment ready
- Test all features beforehand

### Presentation Tips
- Speak confidently and clearly
- Use the prospect's name when possible
- Pause for questions but keep momentum
- Focus on benefits, not just features
- Have real customer stories ready

### Common Questions & Responses

**Q: "How is this different from Google Photos?"**
**A:** "Google Photos is great for basic storage, but can Google guarantee they can't see your photos? PhotoVault uses zero-knowledge encryption - we literally cannot access your photos. Plus, our AI is specifically trained for professional workflows."

**Q: "What if I want to export my data?"**
**A:** "PhotoVault supports full data export in standard formats. You own your photos and can download everything anytime. We earn your business by providing value, not by trapping your data."

**Q: "Is it secure enough for professional use?"**
**A:** "PhotoVault uses the same encryption standards as banks and government agencies. We're SOC 2 compliant and provide complete audit trails. Many professional photographers trust us with their entire business."

### Follow-up Actions
1. Send demo recording link
2. Provide trial account access
3. Schedule technical deep-dive if needed
4. Connect with customer success team
5. Send pricing and implementation timeline
```

## 🛠️ Developer Quick Reference

### Essential Commands Cheat Sheet
Create `developer_commands.md`:

```markdown
# PhotoVault Developer Commands Cheat Sheet

## Backend (Django) Commands

### Environment Setup
```bash
# Create virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Activate (Linux/Mac)
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Database Operations
```bash
# Create migrations
python manage.py makemigrations

# Apply migrations  
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Reset database
python manage.py flush

# Load sample data
python manage.py shell -c "exec(open('create_demo_data.py').read())"
```

### Development Server
```bash
# Start development server
python manage.py runserver 0.0.0.0:8000

# Start with specific port
python manage.py runserver 8080

# Start with debug toolbar
python manage.py runserver --settings=photovault.settings_debug
```

### Testing & Quality
```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test apps.users

# Run with coverage
coverage run --source='.' manage.py test
coverage report
coverage html

# Check code style
flake8 .
black .
isort .
```

### Debugging & Maintenance
```bash
# Django shell
python manage.py shell

# Check for issues
python manage.py check

# Collect static files
python manage.py collectstatic

# Clear cache
python manage.py shell -c "from django.core.cache import cache; cache.clear()"

# Show migrations
python manage.py showmigrations

# SQL for migration
python manage.py sqlmigrate users 0001
```

## Frontend (Next.js) Commands

### Environment Setup
```bash
# Install dependencies
npm install

# Install specific package
npm install package-name

# Install dev dependency
npm install -D package-name
```

### Development Server
```bash
# Start development server
npm run dev

# Start on specific port
npm run dev -- -p 3001

# Start with turbo
npm run dev -- --turbo
```

### Building & Deployment
```bash
# Build for production
npm run build

# Start production server
npm start

# Export static site
npm run export

# Analyze bundle
npm run analyze
```

### Testing & Quality
```bash
# Run tests
npm test

# Run tests in watch mode
npm run test:watch

# Run tests with coverage
npm run test:coverage

# Lint code
npm run lint

# Fix linting issues
npm run lint:fix

# Format code
npm run format
```

### Package Management
```bash
# Update dependencies
npm update

# Check outdated packages
npm outdated

# Audit security
npm audit

# Fix security issues
npm audit fix
```

## Git Workflow Commands

### Basic Operations
```bash
# Clone repository
git clone <repository-url>

# Check status
git status

# Add files
git add .
git add specific-file.py

# Commit changes
git commit -m "Add new feature"

# Push changes
git push origin main
```

### Branch Management
```bash
# Create new branch
git checkout -b feature/new-feature

# Switch branches
git checkout main
git checkout feature/new-feature

# List branches
git branch
git branch -r  # remote branches

# Delete branch
git branch -d feature/old-feature
```

### Advanced Operations
```bash
# Stash changes
git stash
git stash pop

# Reset changes
git reset --hard HEAD

# View commit history
git log --oneline

# Cherry pick commit
git cherry-pick <commit-hash>

# Rebase branch
git rebase main
```

## Docker Commands

### Basic Operations
```bash
# Build images
docker-compose build

# Start services
docker-compose up

# Start in background
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs
docker-compose logs backend
```

### Maintenance
```bash
# Rebuild and start
docker-compose up --build

# Remove volumes
docker-compose down -v

# Clean up
docker system prune

# Shell into container
docker-compose exec backend bash
docker-compose exec frontend sh
```

## Useful One-Liners

### Backend
```bash
# Quick test user creation
python manage.py shell -c "from apps.users.models import User; User.objects.create_user('test@example.com', 'password123', name='Test User', email_verified=True)"

# Reset admin password
python manage.py shell -c "from apps.users.models import User; u = User.objects.get(email='admin@photovault.com'); u.set_password('newpassword'); u.save()"

# Count objects
python manage.py shell -c "from apps.images.models import Image; print(f'Total images: {Image.objects.count()}')"

# Clear all images
python manage.py shell -c "from apps.images.models import Image; Image.objects.all().delete()"
```

### Frontend
```bash
# Clear Next.js cache
rm -rf .next

# Install and add to package.json
npm install --save package-name

# Run specific script
npm run build && npm start

# Check bundle size
npm run build && npm run analyze
```

### System
```bash
# Find process on port
lsof -i :8000  # Mac/Linux
netstat -ano | findstr :8000  # Windows

# Kill process on port
kill -9 $(lsof -t -i:8000)  # Mac/Linux

# Check disk space
df -h  # Linux/Mac
dir  # Windows
```

## Environment Variables Quick Reference

### Backend (.env)
```bash
DEBUG=True
SECRET_KEY=your-secret-key
DATABASE_URL=sqlite:///db.sqlite3
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0
CORS_ALLOWED_ORIGINS=http://localhost:3000
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

### Frontend (.env.local)
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_APP_NAME=PhotoVault
NEXT_PUBLIC_APP_VERSION=1.0.0
```

## Troubleshooting Quick Fixes

### Common Backend Issues
```bash
# Migration conflicts
python manage.py migrate --fake-initial

# Permission denied
chmod +x manage.py

# Port already in use
python manage.py runserver 8001

# Database locked
rm db.sqlite3 && python manage.py migrate
```

### Common Frontend Issues
```bash
# Module not found
rm -rf node_modules && npm install

# Port in use
npm run dev -- -p 3001

# Build errors
rm -rf .next && npm run build

# Cache issues
npm start -- --reset-cache
```
```

These scripts provide comprehensive coverage for both developer and marketing needs, making PhotoVault easy to understand, set up, and demonstrate across different audiences and technical skill levels.