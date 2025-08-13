import os
from datetime import timedelta
from pathlib import Path
import environ
import dj_database_url 

# Initialize environ
env = environ.Env(
    DEBUG=(bool, False)
)

# Set base directory and load .env
BASE_DIR = Path(__file__).resolve().parent.parent
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

# Core settings
SECRET_KEY = env('SECRET_KEY')
DEBUG = env('DEBUG')
ALLOWED_HOSTS = ["*"]

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Installed apps
INSTALLED_APPS = [
    "jazzmin",
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'corsheaders',  # Added corsheaders here

    'rest_framework',
    'rest_framework_simplejwt.token_blacklist',
    'users',
    'plans',
    'classes',
    'payments',
]

CSRF_TRUSTED_ORIGINS = [
    "https://gamplandjango-2.onrender.com",
    "https://gameplan-demo.vercel.app"
]

# Middleware
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',  # Added cors middleware here
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',  # Must be after cors middleware
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# JWT config
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=env.int('ACCESS_TOKEN_EXPIRE_MINUTES')),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=30),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
}

# Root URLs and WSGI
ROOT_URLCONF = 'app.urls'
WSGI_APPLICATION = 'app.wsgi.application'

# Templates
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# Database
# DATABASES = {
#     'default': {
#         'ENGINE': env('DB_ENGINE'),
#         'NAME': env('DB_NAME'),
#         'USER': env('DB_USER'),
#         'PASSWORD': env('DB_PASSWORD'),
#         'HOST': env('DB_HOST'),
#         'PORT': env('DB_PORT'),
#         'OPTIONS': {
#             'options': '-c search_path=django'
#         }
#     }
# }

# Login / Logout redirects (for session-based login)
LOGIN_REDIRECT_URL = env('FRONTEND_DOMAIN') + "/login"
LOGOUT_REDIRECT_URL = env('FRONTEND_DOMAIN') + "/login"


DATABASES = {
    'default': dj_database_url.config(
        default='postgresql://game_ob55_user:TV7YOJcvQurBCRRLRqlm2x3F5CJHX79x@dpg-d2dpvvbuibrs73afvrp0-a.oregon-postgres.render.com/game_ob55',
        conn_max_age=600,
        ssl_require=True
    )
}


# Custom user model
AUTH_USER_MODEL = 'users.User'

# Localization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Dhaka'
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = '/static/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Django REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 5,  
}

# Email settings
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = env('EMAIL_HOST')
EMAIL_PORT = env.int('EMAIL_PORT')
EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS')
EMAIL_HOST_USER = env('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL')

# OAuth credentials
GOOGLE_CLIENT_ID = env('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = env('GOOGLE_CLIENT_SECRET')
FACEBOOK_CLIENT_ID = env('FACEBOOK_CLIENT_ID')
FACEBOOK_CLIENT_SECRET = env('FACEBOOK_CLIENT_SECRET')
GOOGLE_REDIRECT_URI = env('GOOGLE_REDIRECT_URI')
FACEBOOK_REDIRECT_URI = env('FACEBOOK_REDIRECT_URI')

# Stripe
STRIPE_PUBLISHABLE_KEY = env('STRIPE_PUBLISHABLE_KEY')
STRIPE_SECRET_KEY = env('STRIPE_SECRET_KEY')
STRIPE_WEBHOOK_SECRET = env('STRIPE_WEBHOOK_SECRET')
STRIPE_PRICE_MONTHLY = env('STRIPE_PRICE_MONTHLY')
STRIPE_PRICE_YEARLY = env('STRIPE_PRICE_YEARLY')

# Domains
FRONTEND_DOMAIN = env('FRONTEND_DOMAIN')
BACKEND_DOMAIN = env('BACKEND_DOMAIN')

# External APIs
GOOGLE_API_KEY = env('GOOGLE_API_KEY')
TAVILY_API_KEY = env('TAVILY_API_KEY')

# CORS settings

CORS_ALLOWED_ORIGINS = [
    "https://gameplan-demo.vercel.app",
]

CORS_ALLOW_CREDENTIALS = True
