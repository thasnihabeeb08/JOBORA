"""
Django settings for jobora project.
"""

from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-deipp2nu%2rn*u02kr(xh^m09!pbe6bpiat!x406w=w#av7bbu'

DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1']

INSTALLED_APPS = [
    # 'debug_toolbar',  # COMMENTED OUT - SAFELY REMOVED
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'core',
    'users',
    'jobs',
    'job_seeker',
    'django_recaptcha', 
    'widget_tweaks',
    'crispy_forms',
    'crispy_bootstrap5',
    'admin_panel',
]

MIDDLEWARE = [
    # 'debug_toolbar.middleware.DebugToolbarMiddleware',  # COMMENTED OUT - SAFELY REMOVED
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'jobora.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
            ],
        },
    },
]

WSGI_APPLICATION = 'jobora.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True

# ========== STATIC FILES CONFIGURATION ==========
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']  # Development static files
STATIC_ROOT = BASE_DIR / 'staticfiles'    # Production static files collection

# ========== MEDIA FILES CONFIGURATION ==========
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ========== AUTHENTICATION SETTINGS ==========
LOGIN_URL = '/users/login/'
LOGIN_REDIRECT_URL = '/company/dashboard/'
LOGOUT_REDIRECT_URL = '/'

# ========== SESSION SETTINGS ==========
SESSION_COOKIE_AGE = 86400
SESSION_SAVE_EVERY_REQUEST = True

# ========== SECURITY SETTINGS ==========
CSRF_TRUSTED_ORIGINS = ['http://localhost:8000', 'http://127.0.0.1:8000']

# ========== FILE UPLOAD SETTINGS ==========
DATA_UPLOAD_MAX_MEMORY_SIZE = 2621440
FILE_UPLOAD_MAX_MEMORY_SIZE = 2621440

# ========== COMPANY MODULE SETTINGS ==========
JOB_POSTING_DURATION_DAYS = 30
MAX_JOBS_PER_COMPANY = 50
MAX_APPLICATIONS_PER_JOB = 500

# ========== RECAPTCHA SETTINGS ==========
RECAPTCHA_PUBLIC_KEY = '#'
RECAPTCHA_PRIVATE_KEY = '#'

# ========== EMAIL CONFIGURATION ==========
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DEFAULT_FROM_EMAIL = '#'

# ========== DEBUG TOOLBAR SETTINGS - SAFELY REMOVED (COMMENTED OUT) ==========
# INTERNAL_IPS = ['127.0.0.1', 'localhost']

# Debug toolbar configuration - SAFELY REMOVED
# DEBUG_TOOLBAR_PANELS = [
#     'debug_toolbar.panels.history.HistoryPanel',
#     'debug_toolbar.panels.versions.VersionsPanel',
#     'debug_toolbar.panels.timer.TimerPanel',
#     'debug_toolbar.panels.settings.SettingsPanel',
#     'debug_toolbar.panels.headers.HeadersPanel',
#     'debug_toolbar.panels.request.RequestPanel',
#     'debug_toolbar.panels.sql.SQLPanel',
#     'debug_toolbar.panels.staticfiles.StaticFilesPanel',
#     'debug_toolbar.panels.templates.TemplatesPanel',
#     'debug_toolbar.panels.cache.CachePanel',
#     'debug_toolbar.panels.signals.SignalsPanel',
#     'debug_toolbar.panels.redirects.RedirectsPanel',
# ]

# DEBUG_TOOLBAR_CONFIG = {
#     'SHOW_TOOLBAR_CALLBACK': lambda request: DEBUG,
#     'RESULTS_CACHE_SIZE': 100,
#     'SHOW_COLLAPSED': True,
#     'SQL_WARNING_THRESHOLD': 100,
# }

# ========== CRISPY FORMS CONFIGURATION ==========
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"