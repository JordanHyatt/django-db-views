import os


INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'qs_views',
    'tests',
]


USE_TZ=True

# Postgres settings used for testing
name = os.getenv('DB_NAME', 'qsviews')
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
DATABASES = {
    'default': default,
    'other': default,
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