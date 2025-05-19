from pathlib import Path
from decouple import config
from datetime import timedelta

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = config('SECRET_KEY')
DEBUG = False
# Ruxsat etilgan domenlar
ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
    "webtest.namspi.uz",
    "ruletka.namspi.uz",
]

# Ruxsat berilgan hostlar
# Ilovalar ro'yxati
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Uchinchi tomon ilovalari
    'rest_framework',  # REST API uchun
    'rest_framework_simplejwt',  # JWT autentifikatsiyasi
    'dbbackup',  # Ma'lumotlar zaxirasi
    # Sizning ilovalaringiz
    'account',  # Autentifikatsiya moduli
    'core',  # Asosiy logika
    'roulette',  # O'yin moduli
    'common',
]
# Middleware sozlamalari
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # bu qatorda bo‘lishi kerak
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django_ratelimit.middleware.RatelimitMiddleware',  # Rate limiting
]
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
ROOT_URLCONF = 'core.urls'
# Template sozlamalari
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],  # templates papkasi
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
WSGI_APPLICATION = 'core.wsgi.application'

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
# Lokalizatsiya va til
LANGUAGE_CODE = 'uz'  # O'zbek tili
TIME_ZONE = 'Asia/Tashkent'
USE_I18N = True
USE_TZ = True
# Statik fayllar (CSS, JS, rasmlar)
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']  # static papkasi
STATIC_ROOT = BASE_DIR / 'staticfiles'
# Media fayllari (foydalanuvchi yuklagan fayllar)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
# Django REST Framework sozlamalari
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
}
# JWT sozlamalari
REST_FRAMEWORK_SIMPLEJWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
}

AUTH_USER_MODEL = 'account.CustomUser'
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]
# Ma'lumotlar zaxirasi sozlamalari
DBBACKUP_STORAGE = 'django.core.files.storage.FileSystemStorage'
DBBACKUP_STORAGE_OPTIONS = {'location': BASE_DIR / 'backups'}
# Rate limiting sozlamalari
RATELIMIT_ENABLE = True
RATELIMIT_RATE = '100/h'  # Soatiga 100 ta so'rov
RATELIMIT_BLOCK = True
# CSRF va xavfsizlik
CSRF_COOKIE_SECURE = False  # Productionda True qiling
SESSION_COOKIE_SECURE = False  # Productionda True qiling
SECURE_SSL_REDIRECT = False  # Productionda True qiling

# CSRF uchun ishonchli manbalar (HTTPS bilan yozilishi shart)
CSRF_TRUSTED_ORIGINS = [
    "http://localhost",
    "http://127.0.0.1",
    "https://webtest.namspi.uz",
    "https://ruletka.namspi.uz",
]

# Login va Logout yo‘nalishlari
LOGIN_URL = '/account/login/'  # Login sahifasi URLi
LOGOUT_URL = '/account/logout/'  # Logout view URLi
LOGIN_REDIRECT_URL = '/'  # Login'dan so‘ng qayerga yo‘naltirish
LOGOUT_REDIRECT_URL = '/account/login/'  # Logoutdan so‘ng qayerga yo‘naltirish

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
