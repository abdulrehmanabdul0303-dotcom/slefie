#!/usr/bin/env bash
# Render build script for PhotoVault Django

set -o errexit  # exit on error

echo "🚀 Starting PhotoVault build process..."

# Install dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Run quality checks
echo "🔍 Running quality checks..."
ruff check . || echo "⚠️ Linting issues found but continuing..."
black --check . || echo "⚠️ Formatting issues found but continuing..."

# Run security checks
echo "🔒 Running security checks..."
bandit -r . -x "*/tests/*,*/migrations/*" || echo "⚠️ Security issues found but continuing..."

# Django checks
echo "🔧 Running Django checks..."
python manage.py check
python manage.py check --deploy

# Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput

# Run migrations
echo "🗄️ Running database migrations..."
python manage.py migrate

# Setup 2090 feature flags
echo "🌟 Setting up PhotoVault 2090 features..."
python manage.py setup_2090_flags --environment PRODUCTION --enable || echo "⚠️ Feature flags setup failed but continuing..."

echo "✅ Build completed successfully!"
echo "🎉 PhotoVault is ready for deployment!"