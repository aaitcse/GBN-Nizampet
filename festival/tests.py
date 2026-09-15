"""End-to-end coverage of the attendee flows and the organiser console."""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Bookmark, Event, Feedback, Photo, PhotoLike, Poll, PollOption, Vote


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

    def test_home_page_renders_day_one(self):
        response = self.client.get(reverse("festival:public_app"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Cyber Beats Live")
        self.assertNotContains(response, "Acoustic Sunset")

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
