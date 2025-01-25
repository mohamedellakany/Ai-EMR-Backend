from .settings import *

# Override settings for production
DEBUG = False
ALLOWED_HOSTS = ['your-production-domain.com']
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True