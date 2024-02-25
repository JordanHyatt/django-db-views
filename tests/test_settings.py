from pathlib import Path
import os, sys


# Add db_views module to path
PROJECT_DIR = Path(__file__).resolve().parent.parent
MODULE_DIR = os.path.join(PROJECT_DIR, 'db_views')
sys.path.append(MODULE_DIR)



INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'db_views',
    'tests',
]


USE_TZ=True

# Postegres settings used for testing
name = os.getenv('DB_NAME', 'dbviews')
user = os.getenv('DB_USER', 'postgres')
host = os.getenv('DB_HOST', 'localhost')
password = os.getenv('DB_PASSWORD', 'postgres')
port = os.getenv('DB_PORT', '5432')

default = {
    'ENGINE':'django.db.backends.postgresql',
    'NAME': name,
    'USER': user,
    'PASSWORD': password,
    'HOST': host,
    'PORT': port,
}
other = default.copy()
other['NAME'] = other.get('NAME') + '_other'
DATABASES = {
    'default': default,
    'other': other,
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

MIDDLEWARE = [
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.i18n",
                "django.template.context_processors.request",
                "django.template.context_processors.static",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]