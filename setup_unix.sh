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