from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

app_name = "festival"

urlpatterns = [
    # ---- public app -------------------------------------------------------
    path("", views.public_app, name="public_app"),
    path("healthz/", views.healthz, name="healthz"),
    path("partials/events/", views.events_partial, name="events_partial"),
    path("partials/gallery/", views.gallery_partial, name="gallery_partial"),
    path("partials/polls/", views.polls_partial, name="polls_partial"),
    path("events/<int:pk>/bookmark/", views.toggle_bookmark, name="toggle_bookmark"),
    path("photos/<int:pk>/like/", views.toggle_like, name="toggle_like"),
    path("photos/upload/", views.upload_photo, name="upload_photo"),
    path("polls/<int:pk>/vote/", views.cast_vote, name="cast_vote"),
    path("feedback/", views.submit_feedback, name="submit_feedback"),
    # ---- organiser console ------------------------------------------------
    path(
        "console/login/",
        auth_views.LoginView.as_view(
            template_name="console/login.html", redirect_authenticated_user=True
        ),
        name="console_login",
    ),
    path("console/logout/", auth_views.LogoutView.as_view(), name="console_logout"),
    path("console/", views.console_overview, name="console_overview"),
    path("console/events/", views.console_events, name="console_events"),
    path("console/events/new/", views.console_event_form, name="console_event_create"),
    path("console/events/<int:pk>/edit/", views.console_event_form, name="console_event_edit"),
    path("console/events/<int:pk>/delete/", views.console_event_delete, name="console_event_delete"),
    path("console/gallery/", views.console_gallery, name="console_gallery"),
    path(
        "console/gallery/<int:pk>/<str:action>/",
        views.console_photo_action,
        name="console_photo_action",
    ),
    path("console/polls/", views.console_polls, name="console_polls"),
    path("console/polls/<int:pk>/<str:action>/", views.console_poll_action, name="console_poll_action"),
    path("console/feedback/", views.console_feedback, name="console_feedback"),
    path("console/feedback/export/", views.console_feedback_export, name="console_feedback_export"),
    path(
        "console/feedback/<int:pk>/<str:action>/",
        views.console_feedback_action,
        name="console_feedback_action",
    ),
]
