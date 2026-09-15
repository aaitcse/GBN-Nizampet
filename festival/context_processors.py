"""Makes the festival branding available to every template."""

from django.conf import settings


def branding(request):
    return {
        "brand": settings.FEST_BRAND,
        "brand_full": settings.FEST_BRAND_FULL,
        "brand_tagline": settings.FEST_TAGLINE,
    }
