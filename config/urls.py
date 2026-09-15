from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve

urlpatterns = [
    path("django-admin/", admin.site.urls),
    path("", include("festival.urls")),
]

# Attendee photo uploads are served by Django itself. That is fine at festival
# scale (a few hundred images); move MEDIA_ROOT to object storage if it grows.
urlpatterns += [
    re_path(r"^media/(?P<path>.*)$", serve, {"document_root": settings.MEDIA_ROOT}),
]
