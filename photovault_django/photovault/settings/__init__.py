"""
Settings package for PhotoVault.
"""
import os

# Determine which settings to use
if os.environ.get('DJANGO_SETTINGS_MODULE') == 'photovault.settings.production':
    from .production import *
else:
    from .base import *