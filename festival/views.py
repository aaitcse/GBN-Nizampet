"""Views for the public festival app and the organiser console."""

import csv
from datetime import date

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.db import IntegrityError, transaction
from django.db.models import Avg, Count, F, Q, Sum, Value
from django.db.models.functions import Greatest
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
from django.views.decorators.http import require_POST

from .forms import EventForm, FeedbackForm, PhotoForm, PhotoUploadForm, PollForm
from .models import Bookmark, Event, Feedback, Photo, PhotoLike, Poll, PollOption, Vote

GALLERY_CATEGORIES = [("All", "All Photos")] + list(Photo.CATEGORY_CHOICES)

# Home screen copy. Placeholder wording - edit these two lists to match the
# real festival before you hand the link to attendees.
VIBE_CHIPS = [
    "\U0001F3B5 Live Music",
    "\U0001F35C Food Village",
    "\U0001F30C Night Lights",
    "\U0001F3A8 Workshops",
    "⚡ Silent Disco",
]

KNOW_BEFORE = [
    {
        "icon": "fa-id-card",
        "colour": "fest-cyan",
        "title": "Entry & ID",
        "body": "Carry your college ID. Gates open 30 minutes before the first set.",
    },
    {
        "icon": "fa-utensils",
        "colour": "fest-accent",
        "title": "Food Village",
        "body": "Stalls run all day. UPI accepted everywhere, veg counters marked.",
    },
    {
        "icon": "fa-van-shuttle",
        "colour": "fest-gold",
        "title": "Getting there",
        "body": "Shuttles from the main road every 20 minutes until the last act.",
    },
    {
        "icon": "fa-kit-medical",
        "colour": "fest-green",
        "title": "Need help?",
        "body": "Volunteers in pink jackets, and a medical tent by the Main Stage.",
    },
]


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def session_key(request):
    """Every attendee gets a session so bookmarks, likes and votes stick."""
    if not request.session.session_key:
        request.session.create()
    return request.session.session_key


def is_ajax(request):
    return request.headers.get("x-requested-with") == "fetch"


def staff_required(view):
    return user_passes_test(
        lambda u: u.is_active and u.is_staff, login_url="festival:console_login"
    )(view)


def events_context(request):
    """Filtered event list plus the filter state the template needs."""
    day = request.GET.get("day") or Event.DAY_CHOICES[0][0]
    query = (request.GET.get("q") or "").strip()
    saved_only = request.GET.get("saved") == "1"
    bookmarked = set(
        Bookmark.objects.filter(session_key=session_key(request)).values_list("event_id", flat=True)
    )

    events = Event.objects.filter(is_published=True, day=day)
    if query:
        events = events.filter(
            Q(title__icontains=query)
            | Q(location__icontains=query)
            | Q(category__icontains=query)
            | Q(description__icontains=query)
        )
    if saved_only:
        events = events.filter(id__in=bookmarked)

    for event in events:
        event.is_bookmarked = event.id in bookmarked

    return {
        "events": events,
        "day_choices": Event.DAY_CHOICES,
        "selected_day": day,
        "search_query": query,
        "saved_only": saved_only,
        "agenda_count": len(bookmarked),
    }


def gallery_context(request):
    category = request.GET.get("category") or "All"
    photos = Photo.objects.filter(is_approved=True)
    if category != "All":
        photos = photos.filter(category=category)

    liked = set(
        PhotoLike.objects.filter(session_key=session_key(request)).values_list("photo_id", flat=True)
    )
    for photo in photos:
        photo.is_liked = photo.id in liked

    return {
        "photos": photos,
        "gallery_categories": GALLERY_CATEGORIES,
        "selected_category": category,
    }


def decorate_poll(poll, voted_option_id=None):
    """Attach percentages and the viewer's own choice to a poll instance."""
    options = list(poll.options.all())
    total = sum(option.votes for option in options)
    for option in options:
        option.pct = option.percentage(total)
        option.is_choice = option.id == voted_option_id
    poll.decorated_options = options
    poll.total = total
    poll.voted_option_id = voted_option_id
    poll.has_voted = voted_option_id is not None
    return poll


def polls_context(request):
    key = session_key(request)
    votes = dict(Vote.objects.filter(session_key=key).values_list("poll_id", "option_id"))
    polls = Poll.objects.filter(is_active=True).prefetch_related("options")
    return {"polls": [decorate_poll(p, votes.get(p.id)) for p in polls]}


def countdown_label():
    """Human phrasing for how far away the festival is."""
    try:
        start = date.fromisoformat(settings.FEST_START_DATE)
        end = date.fromisoformat(settings.FEST_END_DATE)
    except (ValueError, AttributeError):
        return ""

    today = timezone.localdate()
    if today < start:
        days = (start - today).days
        return "Starts tomorrow" if days == 1 else f"Starts in {days} days"
    if today <= end:
        return f"Live now - day {(today - start).days + 1}"
    return "That is a wrap. See you next year!"


def home_context(request):
    """Everything the landing tab shows: hero, teasers and festival facts."""
    photos = list(Photo.objects.filter(is_approved=True)[:7])
    upcoming = list(Event.objects.filter(is_published=True)[:3])
    poll = Poll.objects.filter(is_active=True).prefetch_related("options").first()

    return {
        "hero_photo": photos[0] if photos else None,
        "home_photos": photos[1:7],
        "home_events": upcoming,
        "home_poll": decorate_poll(poll) if poll else None,
        "home_stats": {
            "events": Event.objects.filter(is_published=True).count(),
            "photos": Photo.objects.filter(is_approved=True).count(),
            "polls": Poll.objects.filter(is_active=True).count(),
        },
        "fest_venue": settings.FEST_VENUE,
        "fest_dates": settings.FEST_DATES,
        "fest_welcome": settings.FEST_WELCOME,
        "fest_countdown": countdown_label(),
        "vibe_chips": VIBE_CHIPS,
        "know_before": KNOW_BEFORE,
    }


# --------------------------------------------------------------------------- #
# public app
# --------------------------------------------------------------------------- #
def public_app(request):
    context = {
        "active_tab": request.GET.get("tab", "home"),
        "feedback_categories": Feedback.CATEGORY_CHOICES,
        "photo_categories": Photo.CATEGORY_CHOICES,
    }
    context.update(events_context(request))
    context.update(gallery_context(request))
    context.update(polls_context(request))
    context.update(home_context(request))
    return render(request, "public/app.html", context)


def events_partial(request):
    return render(request, "public/partials/events_list.html", events_context(request))


def gallery_partial(request):
    return render(request, "public/partials/gallery_grid.html", gallery_context(request))


def polls_partial(request):
    return render(request, "public/partials/polls_list.html", polls_context(request))


@require_POST
def toggle_bookmark(request, pk):
    event = get_object_or_404(Event, pk=pk, is_published=True)
    key = session_key(request)
    bookmark = Bookmark.objects.filter(event=event, session_key=key).first()
    if bookmark:
        bookmark.delete()
        saved = False
    else:
        Bookmark.objects.create(event=event, session_key=key)
        saved = True

    count = Bookmark.objects.filter(session_key=key).count()
    if is_ajax(request):
        return JsonResponse({"saved": saved, "agenda_count": count, "event_id": event.id})
    return redirect(request.META.get("HTTP_REFERER", reverse("festival:public_app")))


@require_POST
def toggle_like(request, pk):
    photo = get_object_or_404(Photo, pk=pk, is_approved=True)
    key = session_key(request)
    like = PhotoLike.objects.filter(photo=photo, session_key=key).first()
    rows = Photo.objects.filter(pk=photo.pk)
    if like:
        like.delete()
        # F() keeps the counter correct when several phones tap at once.
        rows.update(likes=Greatest(F("likes") - 1, Value(0)))
        liked = False
    else:
        PhotoLike.objects.create(photo=photo, session_key=key)
        rows.update(likes=F("likes") + 1)
        liked = True
    photo.refresh_from_db(fields=["likes"])

    if is_ajax(request):
        return JsonResponse({"liked": liked, "likes": photo.likes, "photo_id": photo.id})
    return redirect(request.META.get("HTTP_REFERER", reverse("festival:public_app")))


@require_POST
def upload_photo(request):
    form = PhotoUploadForm(request.POST, request.FILES)
    if form.is_valid():
        photo = form.save(commit=False)
        photo.is_approved = settings.FEST_AUTO_APPROVE_PHOTOS
        photo.save()
        note = (
            "Photo published to the gallery!"
            if photo.is_approved
            else "Photo submitted - an organiser will approve it shortly."
        )
        if is_ajax(request):
            return JsonResponse({"ok": True, "message": note, "approved": photo.is_approved})
        messages.success(request, note)
        return redirect(reverse("festival:public_app") + "?tab=gallery")

    if is_ajax(request):
        return JsonResponse({"ok": False, "errors": form.errors}, status=400)
    messages.error(request, "Could not upload that photo. Check the form and try again.")
    return redirect(reverse("festival:public_app") + "?tab=gallery")


@require_POST
def cast_vote(request, pk):
    poll = get_object_or_404(Poll, pk=pk, is_active=True)
    option = get_object_or_404(PollOption, pk=request.POST.get("option"), poll=poll)
    key = session_key(request)

    try:
        # The savepoint keeps an outer transaction usable if the unique
        # constraint (one vote per poll per session) rejects this insert.
        with transaction.atomic():
            Vote.objects.create(poll=poll, option=option, session_key=key)
    except IntegrityError:
        # Already voted on this poll - just show them the standings again.
        existing = Vote.objects.get(poll=poll, session_key=key)
        if is_ajax(request):
            return render(
                request,
                "public/partials/poll_card.html",
                {"poll": decorate_poll(poll, existing.option_id)},
            )
        return redirect(reverse("festival:public_app") + "?tab=polls")

    PollOption.objects.filter(pk=option.pk).update(votes=F("votes") + 1)
    option.refresh_from_db(fields=["votes"])

    if is_ajax(request):
        return render(
            request, "public/partials/poll_card.html", {"poll": decorate_poll(poll, option.id)}
        )
    return redirect(reverse("festival:public_app") + "?tab=polls")


@require_POST
def submit_feedback(request):
    form = FeedbackForm(request.POST)
    if form.is_valid():
        form.save()
        if is_ajax(request):
            return JsonResponse({"ok": True})
        messages.success(request, "Thank you! Your feedback reached the organisers.")
        return redirect(reverse("festival:public_app") + "?tab=feedback")

    if is_ajax(request):
        return JsonResponse({"ok": False, "errors": form.errors}, status=400)
    messages.error(request, "Please add a comment before submitting.")
    return redirect(reverse("festival:public_app") + "?tab=feedback")


# --------------------------------------------------------------------------- #
# organiser console
# --------------------------------------------------------------------------- #
@staff_required
def console_overview(request):
    photo_stats = Photo.objects.aggregate(
        total=Count("id"),
        approved=Count("id", filter=Q(is_approved=True)),
        pending=Count("id", filter=Q(is_approved=False)),
        likes=Sum("likes"),
    )
    feedback_stats = Feedback.objects.aggregate(
        total=Count("id"),
        unresolved=Count("id", filter=Q(is_resolved=False)),
        average=Avg("rating"),
    )
    context = {
        "section": "overview",
        "total_events": Event.objects.count(),
        "published_events": Event.objects.filter(is_published=True).count(),
        "photo_stats": photo_stats,
        "feedback_stats": feedback_stats,
        "active_polls": Poll.objects.filter(is_active=True).count(),
        "total_polls": Poll.objects.count(),
        "total_votes": Vote.objects.count(),
        "total_bookmarks": Bookmark.objects.count(),
        "recent_feedback": Feedback.objects.all()[:5],
        "pending_photos": Photo.objects.filter(is_approved=False)[:4],
        "top_events": Event.objects.annotate(saves=Count("bookmarks")).order_by("-saves")[:5],
    }
    return render(request, "console/overview.html", context)


@staff_required
def console_events(request):
    events = Event.objects.annotate(saves=Count("bookmarks"))
    day = request.GET.get("day")
    if day:
        events = events.filter(day=day)
    return render(
        request,
        "console/events.html",
        {
            "section": "events",
            "events": events,
            "day_choices": Event.DAY_CHOICES,
            "selected_day": day or "",
        },
    )


@staff_required
def console_event_form(request, pk=None):
    event = get_object_or_404(Event, pk=pk) if pk else None
    if request.method == "POST":
        form = EventForm(request.POST, request.FILES, instance=event)
        if form.is_valid():
            saved = form.save()
            messages.success(request, f"Event '{saved.title}' saved.")
            return redirect("festival:console_events")
    else:
        form = EventForm(instance=event)
    return render(
        request, "console/event_form.html", {"section": "events", "form": form, "event": event}
    )


@staff_required
@require_POST
def console_event_delete(request, pk):
    event = get_object_or_404(Event, pk=pk)
    title = event.title
    event.delete()
    messages.success(request, f"Event '{title}' deleted.")
    return redirect("festival:console_events")


@staff_required
def console_gallery(request):
    form = PhotoForm()
    if request.method == "POST":
        form = PhotoForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Photo added to the gallery.")
            return redirect("festival:console_gallery")

    status = request.GET.get("status", "all")
    photos = Photo.objects.annotate(like_records=Count("photo_likes"))
    if status == "pending":
        photos = photos.filter(is_approved=False)
    elif status == "approved":
        photos = photos.filter(is_approved=True)

    return render(
        request,
        "console/gallery.html",
        {
            "section": "gallery",
            "photos": photos,
            "status": status,
            "form": form,
            "pending_count": Photo.objects.filter(is_approved=False).count(),
        },
    )


@staff_required
@require_POST
def console_photo_action(request, pk, action):
    photo = get_object_or_404(Photo, pk=pk)
    if action == "approve":
        photo.is_approved = True
        photo.save(update_fields=["is_approved"])
        messages.success(request, f"'{photo.title}' is now live in the gallery.")
    elif action == "hide":
        photo.is_approved = False
        photo.save(update_fields=["is_approved"])
        messages.info(request, f"'{photo.title}' hidden from the gallery.")
    elif action == "delete":
        title = photo.title
        photo.delete()
        messages.success(request, f"'{title}' deleted.")
    return redirect(request.META.get("HTTP_REFERER", reverse("festival:console_gallery")))


@staff_required
def console_polls(request):
    form = PollForm()
    if request.method == "POST":
        form = PollForm(request.POST)
        if form.is_valid():
            poll = form.save()
            messages.success(request, f"Poll '{poll.question}' published.")
            return redirect("festival:console_polls")

    polls = [decorate_poll(p) for p in Poll.objects.prefetch_related("options")]
    return render(request, "console/polls.html", {"section": "polls", "polls": polls, "form": form})


@staff_required
@require_POST
def console_poll_action(request, pk, action):
    poll = get_object_or_404(Poll, pk=pk)
    if action == "toggle":
        poll.is_active = not poll.is_active
        poll.save(update_fields=["is_active"])
        messages.info(request, "Poll opened." if poll.is_active else "Poll closed.")
    elif action == "reset":
        poll.options.update(votes=0)
        poll.votes.all().delete()
        messages.success(request, "Poll counters reset to zero.")
    elif action == "delete":
        question = poll.question
        poll.delete()
        messages.success(request, f"Poll '{question}' deleted.")
    return redirect("festival:console_polls")


@staff_required
def console_feedback(request):
    entries = Feedback.objects.all()
    category = request.GET.get("category")
    status = request.GET.get("status")
    if category:
        entries = entries.filter(category=category)
    if status == "open":
        entries = entries.filter(is_resolved=False)
    elif status == "resolved":
        entries = entries.filter(is_resolved=True)

    return render(
        request,
        "console/feedback.html",
        {
            "section": "feedback",
            "entries": entries,
            "categories": Feedback.CATEGORY_CHOICES,
            "selected_category": category or "",
            "status": status or "",
            "average": Feedback.objects.aggregate(avg=Avg("rating"))["avg"],
            "open_count": Feedback.objects.filter(is_resolved=False).count(),
        },
    )


@staff_required
@require_POST
def console_feedback_action(request, pk, action):
    entry = get_object_or_404(Feedback, pk=pk)
    if action == "toggle":
        entry.is_resolved = not entry.is_resolved
        entry.save(update_fields=["is_resolved"])
    elif action == "delete":
        entry.delete()
        messages.success(request, "Feedback entry deleted.")
    return redirect(request.META.get("HTTP_REFERER", reverse("festival:console_feedback")))


@staff_required
def console_feedback_export(request):
    response = HttpResponse(content_type="text/csv")
    stamp = timezone.localtime().strftime("%Y%m%d-%H%M")
    brand = slugify(settings.FEST_BRAND) or "festival"
    response["Content-Disposition"] = f'attachment; filename="{brand}-feedback-{stamp}.csv"'
    writer = csv.writer(response)
    writer.writerow(["Submitted", "Rating", "Category", "Comment", "Contact", "Resolved"])
    for entry in Feedback.objects.all():
        writer.writerow(
            [
                timezone.localtime(entry.created_at).strftime("%Y-%m-%d %H:%M"),
                entry.rating,
                entry.category,
                entry.comment,
                entry.contact,
                "yes" if entry.is_resolved else "no",
            ]
        )
    return response
