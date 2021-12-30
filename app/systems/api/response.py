from django.http import HttpResponse
from rest_framework.response import Response

from systems.encryption.cipher import Cipher


class EncryptedResponse(Response):

    api_type = None

    def __init__(self, user = None, api_type = None, **kwargs):
        super().__init__(**kwargs)
        self.user = user

        if api_type:
            self.api_type = api_type

    @property
    def rendered_content(self):
        if not self.api_type:
            return super().rendered_content
        return Cipher.get(self.api_type, user = self.user).encrypt(super().rendered_content)


class EncryptedCSVResponse(HttpResponse):

    api_type = None

    def __init__(self, user = None, api_type = None, **kwargs):
        super().__init__(**kwargs)
        self.user = user

        if api_type:
            self.api_type = api_type

    @property
    def content(self):
        if not self.api_type:
            return super().content
        return Cipher.get(self.api_type, user = self.user).encrypt(super().content)
