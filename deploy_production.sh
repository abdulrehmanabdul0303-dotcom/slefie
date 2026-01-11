#!/bin/bash

# PhotoVault Elite Production Deployment Script
# Run this script to deploy PhotoVault to production

set -e  # Exit on any error

echo "🚀 PhotoVault Elite Production Deployment"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   print_error "This script should not be run as root for security reasons"
   exit 1
fi

# Check prerequisites
print_info "Checking prerequisites..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Check if .env.production exists
if [ ! -f "photovault_django/.env.production" ]; then
    print_error ".env.production file not found. Please create it from .env.production template."
    exit 1
fi

print_status "Prerequisites check passed"

# Phase 0: Baseline Audit
print_info "Phase 0: Running baseline audit..."

cd photovault_django

# Check git status
if [ -n "$(git status --porcelain)" ]; then
    print_warning "Working directory is not clean. Uncommitted changes detected."
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Django deploy check
print_info "Running Django deployment checks..."
if python manage.py check --deploy --settings=photovault.settings; then
    print_status "Django deployment checks passed"
else
    print_error "Django deployment checks failed"
    exit 1
fi

# Check migrations
print_info "Checking migrations..."
if python manage.py makemigrations --check --dry-run --settings=photovault.settings; then
    print_status "No pending migrations"
else
    print_error "Pending migrations detected"
    exit 1
fi

# Phase 1: Security Check
print_info "Phase 1: Running security checks..."

# Check for secrets in code
if git grep -n "SECRET_KEY\|password\|apikey" . | grep -v ".env" | grep -v "example" | grep -v "template"; then
    print_error "Potential secrets found in code"
    exit 1
else
    print_status "No secrets found in code"
fi

# Phase 2: Code Quality
print_info "Phase 2: Running code quality checks..."

# Install quality tools if not present
pip install -q ruff black bandit pip-audit pytest

# Lint check
if ruff check .; then
    print_status "Linting passed"
else
    print_error "Linting failed"
    exit 1
fi

# Format check
if black --check .; then
    print_status "Code formatting is correct"
else
    print_error "Code formatting issues found"
    exit 1
fi

# Security scan
if bandit -r . -x tests/ -q; then
    print_status "Security scan passed"
else
    print_warning "Security scan found issues (review manually)"
fi

# Dependency vulnerability scan
if pip-audit; then
    print_status "Dependency scan passed"
else
    print_warning "Dependency vulnerabilities found (review manually)"
fi

# Phase 3: Test Suite
print_info "Phase 3: Running test suite..."

# Run API tests
if python ../test_api_direct.py; then
    print_status "API tests passed"
else
    print_error "API tests failed"
    exit 1
fi

# Phase 4: Build and Deploy
print_info "Phase 4: Building and deploying..."

cd ..

# Create production environment
print_info "Setting up production environment..."

# Generate secure secrets if needed
if grep -q "CHANGE-THIS" photovault_django/.env.production; then
    print_warning "Default secrets detected in .env.production"
    print_info "Generating secure secrets..."
    
    # Generate Django secret key
    DJANGO_SECRET=$(python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")
    
    # Generate encryption key
    ENCRYPTION_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
    
    # Generate database password
    DB_PASSWORD=$(python -c "import secrets; print(secrets.token_urlsafe(16))")
    
    # Update .env.production
    sed -i "s/SECRET_KEY=CHANGE-THIS-TO-A-SECURE-SECRET-KEY-IN-PRODUCTION/SECRET_KEY=$DJANGO_SECRET/" photovault_django/.env.production
    sed -i "s/PHOTOVAULT_ENCRYPTION_KEY=CHANGE-THIS-TO-A-32-CHAR-ENCRYPTION-KEY/PHOTOVAULT_ENCRYPTION_KEY=$ENCRYPTION_KEY/" photovault_django/.env.production
    sed -i "s/CHANGE-THIS-PASSWORD/$DB_PASSWORD/g" photovault_django/.env.production
    
    print_status "Secure secrets generated"
fi

# Set environment variables for Docker Compose
export POSTGRES_PASSWORD=$(grep "DATABASE_URL" photovault_django/.env.production | cut -d':' -f3 | cut -d'@' -f1)

# Build Docker images
print_info "Building Docker images..."
if docker-compose -f photovault_django/docker-compose.prod.yml build; then
    print_status "Docker images built successfully"
else
    print_error "Docker build failed"
    exit 1
fi

# Start services
print_info "Starting production services..."
if docker-compose -f photovault_django/docker-compose.prod.yml up -d; then
    print_status "Services started successfully"
else
    print_error "Failed to start services"
    exit 1
fi

# Wait for services to be ready
print_info "Waiting for services to be ready..."
sleep 30

# Run migrations
print_info "Running database migrations..."
if docker-compose -f photovault_django/docker-compose.prod.yml exec -T web python manage.py migrate; then
    print_status "Migrations completed"
else
    print_error "Migration failed"
    exit 1
fi

# Create superuser if needed
print_info "Creating superuser (if needed)..."
docker-compose -f photovault_django/docker-compose.prod.yml exec -T web python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(is_superuser=True).exists():
    User.objects.create_superuser('admin', 'admin@photovault.com', 'admin123')
    print('Superuser created: admin / admin123')
else:
    print('Superuser already exists')
"

# Phase 5: Smoke Tests
print_info "Phase 5: Running smoke tests..."

# Wait a bit more for services to fully start
sleep 10

# Test health endpoint
if curl -f http://localhost:8000/health/ > /dev/null 2>&1; then
    print_status "Health check passed"
else
    print_error "Health check failed"
    docker-compose -f photovault_django/docker-compose.prod.yml logs web
    exit 1
fi

# Test ready endpoint
if curl -f http://localhost:8000/ready/ > /dev/null 2>&1; then
    print_status "Ready check passed"
else
    print_error "Ready check failed"
    exit 1
fi

# Test API endpoint
if curl -f http://localhost:8000/api/auth/csrf/ > /dev/null 2>&1; then
    print_status "API endpoint accessible"
else
    print_error "API endpoint failed"
    exit 1
fi

# Phase 6: Final Status
print_info "Phase 6: Deployment complete!"

echo ""
echo "🎉 PhotoVault Production Deployment Successful!"
echo "=============================================="
echo ""
echo "Services Status:"
docker-compose -f photovault_django/docker-compose.prod.yml ps
echo ""
echo "Access URLs:"
echo "  - Health Check: http://localhost:8000/health/"
echo "  - API Documentation: http://localhost:8000/docs/"
echo "  - Admin Panel: http://localhost:8000/admin/"
echo "  - Frontend: http://localhost:3000/ (if configured)"
echo ""
echo "Default Admin Credentials:"
echo "  - Username: admin"
echo "  - Password: admin123"
echo "  - ⚠️  CHANGE THESE IMMEDIATELY IN PRODUCTION!"
echo ""
echo "Next Steps:"
echo "  1. Configure your domain and SSL certificates"
echo "  2. Set up monitoring and alerting"
echo "  3. Configure backups"
echo "  4. Update admin credentials"
echo "  5. Test client delivery functionality"
echo ""
print_status "PhotoVault is now running in production mode!"

# Show logs
print_info "Showing recent logs (press Ctrl+C to exit):"
docker-compose -f photovault_django/docker-compose.prod.yml logs -f --tail=50