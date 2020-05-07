"""
For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.0/ref/settings/
"""
import os

#-------------------------------------------------------------------------------
# Global settings

#-------------------------------------------------------------------------------
# Core Django settings

#-------------------------------------------------------------------------------
# Django Addons

#
# API configuration
#
ROOT_URLCONF = 'services.data.urls'

REST_FRAMEWORK = {
    'UNAUTHENTICATED_USER': None,
    'DEFAULT_SCHEMA_CLASS': 'systems.api.schema.data.DataSchema',
    'DEFAULT_AUTHENTICATION_CLASSES': [
        # 'systems.api.auth.EncryptedAPITokenAuthentication'
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        # 'rest_framework.permissions.IsAuthenticated'
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'systems.api.schema.renderers.DataJSONRenderer'
    ],
    'DEFAULT_FILTER_BACKENDS': [],
    'SEARCH_PARAM': 'q',
    'COERCE_DECIMAL_TO_STRING': False
}
