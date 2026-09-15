"""Load a realistic demo festival so the app is not empty on first run.

    python manage.py seed_demo            # add demo content
    python manage.py seed_demo --reset    # wipe festival data first
    python manage.py seed_demo --admin    # also create the demo organiser login
"""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from festival.models import Bookmark, Event, Feedback, Photo, PhotoLike, Poll, PollOption, Vote

UNSPLASH = "https://images.unsplash.com/photo-{}?auto=format&fit=crop&w=800&q=80"

EVENTS = [
    ("Cyber Beats Live (Headliner)", "Day 1", "19:00 - 21:00", "Main Stage", "Music",
     "The opening-night headline set: 4K visuals, live drums and a laser wall.",
     "1470225620780-dba8ba36b745"),
    ("Street Food Extravaganza", "Day 1", "12:00 - 22:00", "Food Village", "Food",
     "Forty stalls, six cuisines, one very long queue for the taco truck.",
     "1555396273-367ea4eb4db5"),
    ("Sunrise Yoga & Sound Bath", "Day 1", "07:00 - 08:00", "Garden Lawn", "Workshop",
     "Slow start to the weekend with singing bowls and a lot of stretching.",
     "1544367567-0f2fcb009e0b"),
    ("Acoustic Sunset Sets", "Day 2", "17:30 - 19:00", "Electro Dome", "Music",
     "Three songwriters, one mic, golden hour behind the dome.",
     "1511671782779-c97d3d27a1d4"),
    ("Indie Battle of the Bands", "Day 2", "14:00 - 16:30", "Second Stage", "Music",
     "Eight campus bands play twenty minutes each. The crowd picks the winner.",
     "1493225457124-a3eb161ffa5f"),
    ("Silent Disco Marathon", "Day 2", "22:00 - 02:00", "Dome Annex", "Show",
     "Three channels, three DJs, zero noise complaints.",
     "1516450360452-9312f5e86fc7"),
    ("Glow Parade & Neon Lightshow", "Day 3", "21:00 - 22:30", "Main Grounds", "Show",
     "The closing parade winds through the grounds and ends in fireworks.",
     "1492684223066-81342ee5ff30"),
    ("Campus Sports Meetup", "Day 3", "10:00 - 13:00", "North Field", "Sports",
     "Five-a-side football, ultimate frisbee and a tug of war final.",
     "1461896836934-ffe607ba8211"),
    ("Closing Ceremony & Awards", "Day 3", "23:00 - 23:45", "Main Stage", "Show",
     "Poll winners announced, volunteers thanked, last song of the weekend.",
     "1514525253161-7a46d19cd819"),
]

PHOTOS = [
    ("Main Stage Lasers", "Stage", "1514525253161-7a46d19cd819", "Festival Crew", True, 42),
    ("Crowd Energy at Sundown", "Crowd", "1492684223066-81342ee5ff30", "Alex M.", True, 89),
    ("Midnight Fireworks", "Night", "1516450360452-9312f5e86fc7", "Sarah K.", True, 64),
    ("Food Truck Neon", "Stage", "1555396273-367ea4eb4db5", "Mark T.", True, 18),
    ("Hands Up Front Row", "Crowd", "1470229722913-7c0e2dbbafd3", "Priya R.", True, 51),
    ("Dome After Dark", "Night", "1459749411175-04bf5292ceea", "Festival Crew", False, 0),
]

POLLS = [
    ("Best Stage Visuals of Night 1?",
     [("Main Stage Neon", 142), ("Electro Dome Lasers", 98), ("Acoustic Garden", 24)], True),
    ("Top Snack at Food Village?",
     [("Gourmet Tacos", 76), ("Vegan Smash Burgers", 110), ("Wood-fired Pizza", 63)], True),
    ("Which act should headline the closing night?",
     [("Cyber Beats", 210), ("The Static Hearts", 134), ("DJ Monsoon", 187)], True),
    ("Was the Day 0 soundcheck loud enough?",
     [("Perfect", 44), ("Too quiet", 12)], False),
]

FEEDBACK = [
    (5, "Sound & Stage", "The sound clarity on the Main Stage was absolute perfection!", "user1@fest.com"),
    (4, "Facilities & Cleanliness", "Restroom lines were manageable, but we need more water stations near the Dome.", ""),
    (3, "Food & Drinks", "Great variety, though the vegan stall sold out by 8pm on Friday.", "priya@example.com"),
    (5, "Security & Safety", "Entry check was quick and the marshals were genuinely friendly.", ""),
    (2, "General Suggestion", "Please publish the shuttle timings in the app - we missed the last bus.", "9876543210"),
]


class Command(BaseCommand):
    help = "Seed the database with demo festival content."

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true", help="Delete existing festival data first")
        parser.add_argument("--admin", action="store_true", help="Create the demo organiser account")

    def handle(self, *args, **options):
        if options["reset"]:
            for model in (Vote, PollOption, Poll, PhotoLike, Photo, Bookmark, Event, Feedback):
                model.objects.all().delete()
            self.stdout.write(self.style.WARNING("Cleared existing festival data."))

        for title, day, slot, place, category, description, photo_id in EVENTS:
            Event.objects.get_or_create(
                title=title,
                defaults={
                    "day": day,
                    "time_slot": slot,
                    "location": place,
                    "category": category,
                    "description": description,
                    "image_url": UNSPLASH.format(photo_id),
                },
            )

        for title, category, photo_id, author, approved, likes in PHOTOS:
            Photo.objects.get_or_create(
                title=title,
                defaults={
                    "category": category,
                    "image_url": UNSPLASH.format(photo_id),
                    "author": author,
                    "is_approved": approved,
                    "likes": likes,
                },
            )

        for question, choices, active in POLLS:
            poll, created = Poll.objects.get_or_create(
                question=question, defaults={"is_active": active}
            )
            if created:
                for position, (text, votes) in enumerate(choices, start=1):
                    PollOption.objects.create(poll=poll, text=text, votes=votes, position=position)

        for rating, category, comment, contact in FEEDBACK:
            Feedback.objects.get_or_create(
                comment=comment,
                defaults={"rating": rating, "category": category, "contact": contact},
            )

        if options["admin"]:
            User = get_user_model()
            user, created = User.objects.get_or_create(
                username="admin",
                defaults={"email": "organiser@gbnfest.test", "is_staff": True, "is_superuser": True},
            )
            if created:
                user.set_password("festpulse123")
                user.save()
                self.stdout.write(self.style.SUCCESS("Created organiser login: admin / festpulse123"))
            else:
                self.stdout.write("Organiser account 'admin' already exists - left untouched.")

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {Event.objects.count()} events, {Photo.objects.count()} photos, "
                f"{Poll.objects.count()} polls, {Feedback.objects.count()} feedback entries."
            )
        )
