import logging
from typing import cast

from django.conf import settings
from django.utils import functional
from requests import Session

logger = logging.getLogger(__name__)


class PostMarkIntegration(Session):
    def __init__(self):
        super().__init__()
        self.api_url = settings.POSTMARK_API_URL
        self.api_key = settings.POSTMARK_API_KEY

    def request(self, method, path="/", *args, **kwargs):
        kwargs.setdefault("headers", {})
        kwargs["headers"]["X-Postmark-Server-Token"] = self.api_key
        kwargs["headers"]["Accept"] = "application/json"
        kwargs["headers"]["Content-Type"] = "application/json"
        return super().request(method, self.api_url + path, *args, **kwargs)

    def send_email_template(self, to: str, template_id: str, data: dict, tag: str | None = None):
        body = {
            "TemplateId": template_id,
            "TemplateModel": data,
            "From": settings.POSTMARK_EMAIL,
            "To": to,
        }
        if tag:
            body["Tag"] = tag
        response = self.post("/email/withTemplate", json=body)
        response.raise_for_status()
        return response.json()


client = cast(
    PostMarkIntegration,
    functional.SimpleLazyObject(lambda: PostMarkIntegration()),
)
