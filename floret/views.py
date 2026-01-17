import logging

from django.conf import settings
from django.http import HttpResponse

logger = logging.getLogger(__name__)


def version(request):
    return HttpResponse(settings.VERSION)
