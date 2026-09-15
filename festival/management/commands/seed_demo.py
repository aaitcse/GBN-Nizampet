"""Load a demo Ganesh Utsav programme so the app is not empty on first run.

    python manage.py seed_demo            # add demo content
    python manage.py seed_demo --reset    # wipe festival data first
    python manage.py seed_demo --admin    # also create the demo organiser login

The schedule below is placeholder programming for a seven day utsav. Edit it,
or replace it from the organiser console once the real timings are fixed. The
images are generic stock photos - swap in real ones from the console.
"""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from festival.models import Bookmark, Event, Feedback, Photo, PhotoLike, Poll, PollOption, Vote

UNSPLASH = "https://images.unsplash.com/photo-{}?auto=format&fit=crop&w=800&q=80"

# Stock image ids, all checked to resolve.
LIGHTS = "1470225620780-dba8ba36b745"
FOOD = "1555396273-367ea4eb4db5"
ACOUSTIC = "1511671782779-c97d3d27a1d4"
CROWD = "1492684223066-81342ee5ff30"
STAGE = "1514525253161-7a46d19cd819"
FIREWORKS = "1516450360452-9312f5e86fc7"
CALM = "1544367567-0f2fcb009e0b"
BAND = "1493225457124-a3eb161ffa5f"
FIELD = "1461896836934-ffe607ba8211"
HANDS = "1470229722913-7c0e2dbbafd3"
NIGHT = "1459749411175-04bf5292ceea"

# title, day, time, place, category, description, image
EVENTS = [
    ("Ganesh Sthapana & Pran Pratishtha", "Day 1", "06:30 - 09:00", "Main Pandal", "Ritual",
     "The idol is installed and the week opens with the first aarti of the utsav.", CALM),
    ("Inaugural Bhajan Sandhya", "Day 1", "18:30 - 20:30", "Main Pandal", "Music",
     "Campus choir and invited singers open the cultural calendar.", ACOUSTIC),

    ("Rangoli Competition", "Day 2", "10:00 - 13:00", "Arts Block", "Workshop",
     "Teams of two, chalk and colour provided, judging at 1 pm.", HANDS),
    ("Dhol Tasha Pathak", "Day 2", "18:00 - 19:30", "Central Lawn", "Music",
     "Forty drummers open the evening. Stand back from the circle.", BAND),

    ("Atharvashirsha Recitation", "Day 3", "06:30 - 07:30", "Main Pandal", "Ritual",
     "Collective morning recitation. Everyone is welcome to join in.", CALM),
    ("Classical Dance Evening", "Day 3", "18:30 - 21:00", "Open Air Theatre", "Show",
     "Bharatanatyam and Kuchipudi sets from students and guest artists.", STAGE),

    ("Eco Ganesha Clay Workshop", "Day 4", "10:00 - 12:30", "Arts Block", "Workshop",
     "Shape your own clay idol to take home. Materials included.", HANDS),
    ("Inter-college Singing Contest", "Day 4", "15:00 - 18:00", "Auditorium", "Music",
     "Twelve colleges, three rounds, one trophy.", ACOUSTIC),

    ("Mahaprasadam Annadanam", "Day 5", "12:00 - 15:00", "Food Village", "Food",
     "Community lunch served to all. Volunteers welcome at the counters.", FOOD),
    ("Garba & Folk Night", "Day 5", "19:00 - 22:00", "Central Lawn", "Show",
     "Live dhol, open floor, no experience needed.", CROWD),

    ("Sports Meet & Tug of War", "Day 6", "09:00 - 13:00", "North Field", "Sports",
     "Department teams, knockout format, finals right before lunch.", FIELD),
    ("Grand Cultural Finale", "Day 6", "18:00 - 22:00", "Open Air Theatre", "Show",
     "The big one: dance, drama, band sets and the prize ceremony.", LIGHTS),

    ("Maha Aarti", "Day 7", "08:00 - 09:15", "Main Pandal", "Ritual",
     "The final aarti before the procession. Pandal fills early.", NIGHT),
    ("Visarjan Procession", "Day 7", "16:00 - 20:00", "Campus Gate to Lake Road", "Show",
     "Procession leaves the campus gate at 4 pm sharp. Walk with the dhol.", FIREWORKS),
]

# title, category, image, author, approved, likes
PHOTOS = [
    ("Sthapana Morning", "Stage", CALM, "Festival Crew", True, 38),
    ("Dhol Tasha Circle", "Crowd", BAND, "Anil K.", True, 92),
    ("Evening Aarti Lamps", "Night", NIGHT, "Sarah K.", True, 71),
    ("Prasadam Counter Rush", "Crowd", FOOD, "Mark T.", True, 24),
    ("Pandal After Dark", "Night", FIREWORKS, "Priya R.", True, 57),
    ("Front Row Hands Up", "Crowd", HANDS, "Festival Fan", False, 0),
]

POLLS = [
    ("Which pandal decoration deserves the prize?",
     [("Eco-friendly clay theme", 142), ("Floral mandap", 98), ("Temple replica", 76)], True),
    ("Best prasadam this year?",
     [("Modak", 210), ("Motichoor laddu", 118), ("Puran poli", 64)], True),
    ("Favourite evening so far?",
     [("Bhajan Sandhya", 88), ("Dhol Tasha", 176), ("Classical Dance", 95)], True),
    ("Should the aarti be live-streamed next year?",
     [("Yes, please", 64), ("No need", 9)], False),
]

FEEDBACK = [
    (5, "Sound & Stage", "The aarti sound reached the whole ground clearly this year. Beautifully done.", "student1@gbn.test"),
    (4, "Facilities & Cleanliness", "Darshan queue moved fast, but we need more bins near the food village.", ""),
    (3, "Food & Drinks", "Prasadam counters ran out by 2 pm on day one. Maybe add a second counter?", "priya@example.com"),
    (5, "Security & Safety", "Volunteers managing the dhol circle did a great job keeping kids safe.", ""),
    (2, "General Suggestion", "Please announce the visarjan route timings in the app a day earlier.", "9876543210"),
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
