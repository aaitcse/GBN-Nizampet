"""End-to-end coverage of the attendee flows and the organiser console."""

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.templatetags.static import static
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .models import (
    Bookmark,
    Event,
    Feedback,
    PageView,
    Photo,
    PhotoLike,
    Poll,
    PollOption,
    Vote,
    category_image,
    current_festival_day,
    festival_banner,
    festival_day_choices,
)
from .views import countdown_label, view_stats


def make_event(**kwargs):
    defaults = {
        "title": "Cyber Beats Live",
        "day": "Day 1",
        "time_slot": "19:00 - 21:00",
        "location": "Main Stage",
        "category": "Music",
        "image_url": "https://example.com/stage.jpg",
    }
    defaults.update(kwargs)
    return Event.objects.create(**defaults)


class PublicAppTests(TestCase):
    def setUp(self):
        self.day1 = make_event()
        self.day2 = make_event(title="Acoustic Sunset", day="Day 2", location="Electro Dome")
        self.draft = make_event(title="Secret Set", is_published=False)
        self.photo = Photo.objects.create(
            title="Main Stage Lasers", category="Stage", image_url="https://example.com/1.jpg",
            is_approved=True, likes=5,
        )
        self.hidden_photo = Photo.objects.create(
            title="Not approved yet", category="Crowd", image_url="https://example.com/2.jpg",
        )
        self.poll = Poll.objects.create(question="Best stage?")
        self.option_a = PollOption.objects.create(poll=self.poll, text="Main", votes=3, position=1)
        self.option_b = PollOption.objects.create(poll=self.poll, text="Dome", votes=1, position=2)

    def test_home_is_the_default_tab(self):
        response = self.client.get(reverse("festival:public_app"))
        self.assertEqual(response.context["active_tab"], "home")
        for block in ["Happening soon", "Straight from the crowd", "Know before you go"]:
            self.assertContains(response, block)

    def test_home_hero_uses_latest_approved_photo(self):
        response = self.client.get(reverse("festival:public_app"))
        self.assertEqual(response.context["hero_photo"], self.photo)

    def test_home_never_shows_unapproved_photos(self):
        response = self.client.get(reverse("festival:public_app"))
        shown = [self.photo] + list(response.context["home_photos"])
        self.assertNotIn(self.hidden_photo, shown)

    @override_settings(FEST_START_DATE="2099-01-10", FEST_END_DATE="2099-01-12")
    def test_countdown_before_the_festival(self):
        self.assertTrue(countdown_label().startswith("Starts in "))

    @override_settings(FEST_START_DATE="2000-01-01", FEST_END_DATE="2000-01-03")
    def test_countdown_after_the_festival(self):
        self.assertIn("wrap", countdown_label())

    @override_settings(FEST_START_DATE="not-a-date", FEST_END_DATE="nope")
    def test_countdown_survives_a_bad_date_setting(self):
        self.assertEqual(countdown_label(), "")

    @override_settings(FEST_START_DATE="2026-09-14", FEST_END_DATE="2026-09-20")
    def test_day_tabs_are_built_from_the_festival_dates(self):
        choices = festival_day_choices()
        self.assertEqual(len(choices), 7)
        self.assertEqual(choices[0], ("Day 1", "Day 1 - Mon 14 Sep"))
        self.assertEqual(choices[-1], ("Day 7", "Day 7 - Sun 20 Sep"))

    @override_settings(FEST_START_DATE="nonsense", FEST_END_DATE="nonsense")
    def test_day_tabs_fall_back_when_dates_are_unset(self):
        self.assertEqual([v for v, _ in festival_day_choices()], ["Day 1", "Day 2", "Day 3"])

    @override_settings(FEST_START_DATE="2026-09-20", FEST_END_DATE="2026-09-14")
    def test_day_tabs_ignore_a_backwards_date_range(self):
        self.assertEqual(len(festival_day_choices()), 3)

    def test_schedule_opens_on_todays_day_during_the_festival(self):
        today = timezone.localdate()
        with override_settings(
            FEST_START_DATE=str(today - timedelta(days=2)),
            FEST_END_DATE=str(today + timedelta(days=4)),
        ):
            self.assertEqual(current_festival_day(), "Day 3")
            response = self.client.get(reverse("festival:public_app"))
            self.assertEqual(response.context["selected_day"], "Day 3")

    def test_schedule_opens_on_day_one_outside_the_festival(self):
        today = timezone.localdate()
        with override_settings(
            FEST_START_DATE=str(today + timedelta(days=30)),
            FEST_END_DATE=str(today + timedelta(days=32)),
        ):
            self.assertEqual(current_festival_day(), "Day 1")

    def test_events_tab_renders_day_one(self):
        response = self.client.get(reverse("festival:public_app"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Cyber Beats Live")
        # Day filtering belongs to the events list; the home carousel is
        # deliberately cross-day, so scope this assertion to the list itself.
        day_one = self.client.get(reverse("festival:events_partial"), {"day": "Day 1"})
        self.assertContains(day_one, "Cyber Beats Live")
        self.assertNotContains(day_one, "Acoustic Sunset")

    def test_unpublished_events_are_hidden(self):
        response = self.client.get(reverse("festival:public_app"))
        self.assertNotContains(response, "Secret Set")

    def test_event_search_and_day_filter(self):
        url = reverse("festival:events_partial")
        self.assertContains(self.client.get(url, {"day": "Day 2"}), "Acoustic Sunset")
        self.assertContains(self.client.get(url, {"day": "Day 2", "q": "dome"}), "Acoustic Sunset")
        self.assertNotContains(self.client.get(url, {"day": "Day 2", "q": "zzz"}), "Acoustic Sunset")

    def test_bookmark_toggles_on_and_off(self):
        url = reverse("festival:toggle_bookmark", args=[self.day1.id])
        first = self.client.post(url, HTTP_X_REQUESTED_WITH="fetch")
        self.assertJSONEqual(
            first.content, {"saved": True, "agenda_count": 1, "event_id": self.day1.id}
        )
        self.assertEqual(Bookmark.objects.count(), 1)

        second = self.client.post(url, HTTP_X_REQUESTED_WITH="fetch")
        self.assertJSONEqual(
            second.content, {"saved": False, "agenda_count": 0, "event_id": self.day1.id}
        )
        self.assertEqual(Bookmark.objects.count(), 0)

    def test_saved_filter_only_returns_bookmarked_events(self):
        self.client.post(
            reverse("festival:toggle_bookmark", args=[self.day1.id]), HTTP_X_REQUESTED_WITH="fetch"
        )
        response = self.client.get(reverse("festival:events_partial"), {"day": "Day 1", "saved": "1"})
        self.assertContains(response, "Cyber Beats Live")

    def test_gallery_shows_only_approved_photos(self):
        response = self.client.get(reverse("festival:gallery_partial"))
        self.assertContains(response, "Main Stage Lasers")
        self.assertNotContains(response, "Not approved yet")

    def test_gallery_category_filter(self):
        response = self.client.get(reverse("festival:gallery_partial"), {"category": "Night"})
        self.assertNotContains(response, "Main Stage Lasers")

    def test_like_is_one_per_session_and_reversible(self):
        url = reverse("festival:toggle_like", args=[self.photo.id])
        liked = self.client.post(url, HTTP_X_REQUESTED_WITH="fetch").json()
        self.assertTrue(liked["liked"])
        self.assertEqual(liked["likes"], 6)
        self.assertEqual(PhotoLike.objects.count(), 1)

        unliked = self.client.post(url, HTTP_X_REQUESTED_WITH="fetch").json()
        self.assertFalse(unliked["liked"])
        self.assertEqual(unliked["likes"], 5)
        self.assertEqual(PhotoLike.objects.count(), 0)

    def test_photo_upload_waits_for_approval(self):
        response = self.client.post(
            reverse("festival:upload_photo"),
            {"title": "My capture", "image_url": "https://example.com/x.jpg", "category": "Crowd",
             "author": "Priya"},
            HTTP_X_REQUESTED_WITH="fetch",
        )
        self.assertEqual(response.status_code, 200)
        photo = Photo.objects.get(title="My capture")
        self.assertFalse(photo.is_approved)
        self.assertNotContains(self.client.get(reverse("festival:gallery_partial")), "My capture")

    def test_photo_upload_requires_a_file_or_url(self):
        response = self.client.post(
            reverse("festival:upload_photo"),
            {"title": "Nothing attached", "category": "Crowd"},
            HTTP_X_REQUESTED_WITH="fetch",
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(Photo.objects.filter(title="Nothing attached").exists())

    def test_vote_counts_once_per_session(self):
        url = reverse("festival:cast_vote", args=[self.poll.id])
        self.client.post(url, {"option": self.option_a.id}, HTTP_X_REQUESTED_WITH="fetch")
        self.option_a.refresh_from_db()
        self.assertEqual(self.option_a.votes, 4)

        # A second vote from the same session must not move the counters.
        self.client.post(url, {"option": self.option_b.id}, HTTP_X_REQUESTED_WITH="fetch")
        self.option_a.refresh_from_db()
        self.option_b.refresh_from_db()
        self.assertEqual(self.option_a.votes, 4)
        self.assertEqual(self.option_b.votes, 1)
        self.assertEqual(Vote.objects.count(), 1)

    def test_vote_response_shows_results(self):
        response = self.client.post(
            reverse("festival:cast_vote", args=[self.poll.id]),
            {"option": self.option_a.id},
            HTTP_X_REQUESTED_WITH="fetch",
        )
        self.assertContains(response, "you already voted")

    def test_closed_polls_are_not_votable(self):
        self.poll.is_active = False
        self.poll.save()
        response = self.client.post(
            reverse("festival:cast_vote", args=[self.poll.id]),
            {"option": self.option_a.id},
            HTTP_X_REQUESTED_WITH="fetch",
        )
        self.assertEqual(response.status_code, 404)

    def test_feedback_submission(self):
        response = self.client.post(
            reverse("festival:submit_feedback"),
            {"rating": 4, "category": "Food & Drinks", "comment": "More water stations please",
             "contact": "fan@example.com"},
            HTTP_X_REQUESTED_WITH="fetch",
        )
        self.assertEqual(response.status_code, 200)
        entry = Feedback.objects.get()
        self.assertEqual(entry.rating, 4)
        self.assertFalse(entry.is_resolved)

    def test_feedback_requires_a_comment(self):
        response = self.client.post(
            reverse("festival:submit_feedback"),
            {"rating": 5, "category": "General Suggestion", "comment": ""},
            HTTP_X_REQUESTED_WITH="fetch",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Feedback.objects.count(), 0)


class EventArtworkTests(TestCase):
    def test_event_without_a_picture_gets_artwork_for_its_category(self):
        event = make_event(category="Sloka", image_url="")
        self.assertEqual(event.display_image, static("img/cat/sloka.png"))

    def test_an_events_own_image_url_always_wins(self):
        event = make_event(category="Dance", image_url="https://example.com/troupe.jpg")
        self.assertEqual(event.display_image, "https://example.com/troupe.jpg")

    def test_unknown_category_falls_back_to_the_festival_banner(self):
        event = make_event(category="Mystery", image_url="")
        self.assertEqual(event.display_image, festival_banner())

    def test_every_category_choice_has_artwork(self):
        for code, _ in Event.CATEGORY_CHOICES:
            with self.subTest(category=code):
                self.assertEqual(
                    category_image(code), static(f"img/cat/{code.lower()}.png")
                )


class ViewCountTests(TestCase):
    def test_opening_the_app_records_a_view_with_its_tab(self):
        self.client.get(reverse("festival:public_app"))
        self.client.get(reverse("festival:public_app"), {"tab": "gallery"})

        self.assertEqual(PageView.objects.count(), 2)
        self.assertEqual(list(PageView.objects.values_list("tab", flat=True)), ["gallery", "home"])

    def test_partials_and_actions_are_not_counted_as_views(self):
        self.client.get(reverse("festival:events_partial"))
        self.client.get(reverse("festival:gallery_partial"))
        self.client.get(reverse("festival:healthz"))
        self.assertEqual(PageView.objects.count(), 0)

    def test_repeat_visits_from_one_device_count_once_as_a_device(self):
        for _ in range(4):
            self.client.get(reverse("festival:public_app"))

        stats = view_stats()
        self.assertEqual(stats["views_total"], 4)
        self.assertEqual(stats["views_devices"], 1)
        self.assertEqual(stats["views_today"], 4)

    def test_daily_breakdown_covers_seven_days_ending_today(self):
        self.client.get(reverse("festival:public_app"))
        daily = view_stats()["views_daily"]

        self.assertEqual(len(daily), 7)
        self.assertEqual(daily[-1]["date"], timezone.localdate())
        self.assertTrue(daily[-1]["is_today"])
        self.assertEqual(daily[-1]["hits"], 1)
        self.assertEqual(daily[-1]["pct"], 100)
        self.assertEqual(sum(row["hits"] for row in daily[:-1]), 0)

    def test_tab_breakdown_percentages(self):
        for tab in ["home", "home", "polls", "events"]:
            self.client.get(reverse("festival:public_app"), {"tab": tab})

        tabs = {row["tab"]: row for row in view_stats()["views_tabs"]}
        self.assertEqual(tabs["home"]["hits"], 2)
        self.assertEqual(tabs["home"]["pct"], 50)
        self.assertEqual(tabs["polls"]["hits"], 1)

    def test_home_shows_the_public_view_counter(self):
        for _ in range(3):
            self.client.get(reverse("festival:public_app"))

        response = self.client.get(reverse("festival:public_app"))
        # The count shown is the one before this load was recorded.
        self.assertEqual(response.context["site_views"], 3)
        self.assertContains(response, "fa-eye")

    def test_console_overview_shows_the_counters(self):
        self.client.get(reverse("festival:public_app"))
        get_user_model().objects.create_user("boss", password="pw12345!", is_staff=True)
        self.client.login(username="boss", password="pw12345!")

        response = self.client.get(reverse("festival:console_overview"))
        self.assertContains(response, "App views")
        self.assertContains(response, "App views, last 7 days")
        self.assertEqual(response.context["views_total"], 1)


class HealthCheckTests(TestCase):
    def test_healthz_reports_ok_on_a_migrated_database(self):
        response = self.client.get(reverse("festival:healthz"))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["ok"])

    def test_healthz_needs_no_login(self):
        self.assertEqual(self.client.get(reverse("festival:healthz")).status_code, 200)


class ConsoleAccessTests(TestCase):
    def test_console_requires_staff_login(self):
        response = self.client.get(reverse("festival:console_overview"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("festival:console_login"), response.url)

    def test_signed_in_non_staff_is_rejected(self):
        get_user_model().objects.create_user("fan", password="pw12345!")
        self.client.login(username="fan", password="pw12345!")
        response = self.client.get(reverse("festival:console_overview"))
        self.assertEqual(response.status_code, 302)


class ConsoleTests(TestCase):
    def setUp(self):
        get_user_model().objects.create_user(
            "organiser", password="pw12345!", is_staff=True, is_superuser=True
        )
        self.client.login(username="organiser", password="pw12345!")
        self.event = make_event()
        self.photo = Photo.objects.create(
            title="Pending shot", category="Crowd", image_url="https://example.com/p.jpg"
        )
        self.feedback = Feedback.objects.create(rating=3, category="Food & Drinks", comment="Slow queue")

    def test_all_console_pages_load(self):
        for name in [
            "festival:console_overview",
            "festival:console_events",
            "festival:console_gallery",
            "festival:console_polls",
            "festival:console_feedback",
            "festival:console_event_create",
        ]:
            with self.subTest(page=name):
                self.assertEqual(self.client.get(reverse(name)).status_code, 200)

    def test_create_event_appears_in_public_app(self):
        response = self.client.post(
            reverse("festival:console_event_create"),
            {"title": "Drone Light Show", "day": "Day 1", "time_slot": "20:00 - 20:30",
             "location": "Main Grounds", "category": "Show", "description": "",
             "image_url": "https://example.com/drone.jpg", "is_published": "on"},
        )
        self.assertRedirects(response, reverse("festival:console_events"))
        self.assertContains(self.client.get(reverse("festival:public_app")), "Drone Light Show")

    def test_event_requires_an_image_source(self):
        response = self.client.post(
            reverse("festival:console_event_create"),
            {"title": "No art", "day": "Day 1", "time_slot": "10:00", "location": "Field",
             "category": "Other", "description": "", "image_url": "", "is_published": "on"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Event.objects.filter(title="No art").exists())

    def test_edit_and_delete_event(self):
        self.client.post(
            reverse("festival:console_event_edit", args=[self.event.id]),
            {"title": "Renamed Set", "day": "Day 3", "time_slot": "22:00", "location": "Dome",
             "category": "Music", "description": "", "image_url": "https://example.com/a.jpg",
             "is_published": "on"},
        )
        self.event.refresh_from_db()
        self.assertEqual(self.event.title, "Renamed Set")
        self.assertEqual(self.event.day, "Day 3")

        self.client.post(reverse("festival:console_event_delete", args=[self.event.id]))
        self.assertFalse(Event.objects.filter(id=self.event.id).exists())

    def test_approving_a_photo_publishes_it(self):
        self.client.post(reverse("festival:console_photo_action", args=[self.photo.id, "approve"]))
        self.photo.refresh_from_db()
        self.assertTrue(self.photo.is_approved)
        self.assertContains(self.client.get(reverse("festival:gallery_partial")), "Pending shot")

    def test_hiding_and_deleting_a_photo(self):
        self.client.post(reverse("festival:console_photo_action", args=[self.photo.id, "approve"]))
        self.client.post(reverse("festival:console_photo_action", args=[self.photo.id, "hide"]))
        self.photo.refresh_from_db()
        self.assertFalse(self.photo.is_approved)

        self.client.post(reverse("festival:console_photo_action", args=[self.photo.id, "delete"]))
        self.assertFalse(Photo.objects.filter(id=self.photo.id).exists())

    def test_create_poll_with_options(self):
        self.client.post(
            reverse("festival:console_polls"),
            {"question": "Best food stall?", "option_1": "Tacos", "option_2": "Burgers",
             "option_3": "", "option_4": "", "is_active": "on"},
        )
        poll = Poll.objects.get(question="Best food stall?")
        self.assertEqual(poll.options.count(), 2)
        self.assertContains(self.client.get(reverse("festival:polls_partial")), "Best food stall?")

    def test_close_and_reset_poll(self):
        poll = Poll.objects.create(question="Loud enough?")
        option = PollOption.objects.create(poll=poll, text="Yes", votes=9)

        self.client.post(reverse("festival:console_poll_action", args=[poll.id, "toggle"]))
        poll.refresh_from_db()
        self.assertFalse(poll.is_active)
        self.assertNotContains(self.client.get(reverse("festival:polls_partial")), "Loud enough?")

        self.client.post(reverse("festival:console_poll_action", args=[poll.id, "reset"]))
        option.refresh_from_db()
        self.assertEqual(option.votes, 0)

    def test_feedback_resolve_toggle_and_export(self):
        self.client.post(reverse("festival:console_feedback_action", args=[self.feedback.id, "toggle"]))
        self.feedback.refresh_from_db()
        self.assertTrue(self.feedback.is_resolved)

        export = self.client.get(reverse("festival:console_feedback_export"))
        self.assertEqual(export["Content-Type"], "text/csv")
        self.assertIn("Slow queue", export.content.decode())
