"""Load the Gokuls Bhuvanam Community Ganesh Chavithi cultural programme.

Transcribed from the day banners (Day 1 Mon 14 Sep .. Day 5 Fri 18 Sep 2026).

    python manage.py load_programme             # add or update the programme
    python manage.py load_programme --replace   # clear existing events first

Idempotent: an item is matched on day + time slot + title, so running it twice
does not duplicate the schedule. Days 6 and 7 are not in the banners yet - add
them here, or straight from the organiser console.
"""

from django.core.management.base import BaseCommand

from festival.models import Event

STAGE = "Community Stage"
ART_AREA = "Community Area"

# (day, time slot, participant or team, category, detail line, location)
PROGRAMME = [
    # ---- Day 1 - Monday 14 September ------------------------------------
    ("Day 1", "7:00 - 7:10 PM", "Adhrit", "Music", "Instrumental Music - 5 min", STAGE),
    ("Day 1", "7:10 - 7:25 PM", "Team 1 - Vaishnika", "Dance", "Kuchipudi - 15 min", STAGE),
    ("Day 1", "7:25 - 7:40 PM", "Team 2 - Shanvi, Aadya", "Dance", "Dance - 15 min", STAGE),
    ("Day 1", "7:40 - 7:55 PM", "Team 3 - Pranavi, Manasvi, Amrutha, Annya & Rishitha", "Dance",
     "Group Dance - 15 min", STAGE),
    ("Day 1", "7:55 - 8:10 PM", "Team 4 - Dyuthi", "Dance", "Dance - 15 min", STAGE),
    ("Day 1", "8:10 - 8:20 PM", "Vaishnavi Vegi", "Sloka", "Sloka Recitation - 5 to 8 min", STAGE),
    ("Day 1", "8:20 - 8:30 PM", "Shanvi, Aadhya", "Dance", "Traditional Dance - 3 min", STAGE),
    ("Day 1", "8:30 - 8:40 PM", "Kode Sri Dhanvi", "Sloka", "Sloka Recitation - 5 to 10 min", STAGE),
    ("Day 1", "8:40 - 8:50 PM", "Kode Praveena", "Sloka", "Sloka Recitation - 5 to 10 min", STAGE),
    ("Day 1", "8:50 - 8:55 PM", "Shanvi Rajanala", "Dance", "Traditional Solo - 5 min", STAGE),
    ("Day 1", "7:00 - 9:00 PM", "Jyotika Amulya", "Art",
     "Art Work Display - throughout the evening, on display in the community area", ART_AREA),

    # ---- Day 2 - Tuesday 15 September -----------------------------------
    ("Day 2", "7:00 - 7:15 PM", "Aarohi Kodumagulla", "Singing", "Singing - 15 min", STAGE),
    ("Day 2", "7:15 - 7:25 PM", "Laasya + Team", "Dance", "Mashup - 10 min", STAGE),
    ("Day 2", "7:25 - 7:31 PM", "Preetika + Rithvika", "Dance", "Mashup - 6 min", STAGE),
    ("Day 2", "7:31 - 7:40 PM", "P. Sai Tanvika", "Singing", "Singing - 8 to 10 min", STAGE),
    ("Day 2", "7:40 - 7:45 PM", "Aaryan Kodumagulla", "Singing", "Singing - 5 min", STAGE),
    ("Day 2", "7:45 - 7:54 PM", "Jhansi", "Singing", "Singing - 9 min", STAGE),
    ("Day 2", "7:54 - 7:59 PM", "P. Ishaan Charan", "Singing", "Singing - 5 min", STAGE),
    ("Day 2", "7:59 - 8:05 PM", "Rithvika", "Dance", "Mashup - 6 min", STAGE),
    ("Day 2", "8:05 - 8:10 PM", "Vaishnavi", "Dance", "Traditional Solo - 5 min", STAGE),
    ("Day 2", "8:10 - 8:20 PM", "Kautilya", "Dance", "Mashup Solo - 10 min", STAGE),
    ("Day 2", "8:20 - 8:25 PM", "Dyuthi + Yogana", "Dance", "Western Group - 5 min", STAGE),

    # ---- Day 3 - Wednesday 16 September ---------------------------------
    ("Day 3", "7:00 - 7:30 PM", "Kala + Team", "Dance", "Traditional - 30 min", STAGE),
    ("Day 3", "7:30 - 7:35 PM", "Neshya Sri", "Dance", "Traditional - 5 min", STAGE),
    ("Day 3", "7:35 - 7:41 PM", "Pranavi, Dyuthi, Yogana, Manasvi, Amrutha & Ananaya", "Dance",
     "Western Group - 6 min", STAGE),
    ("Day 3", "7:41 - 7:43 PM", "Kushvitha", "Dance", "Mashup - 1 to 2 min", STAGE),
    ("Day 3", "7:43 - 7:49 PM", "P. Sai Tanvika", "Dance", "Mashup - 6 min", STAGE),
    ("Day 3", "7:49 - 7:52 PM", "Riyaansh Vasavan", "Sloka", "Sloka Recitation - 3 min", STAGE),
    ("Day 3", "7:52 - 8:02 PM", "Jayaswee Manasa & Riyaansh Vasavan", "Sloka",
     "Sloka Recitation & Singing - 10 min", STAGE),
    ("Day 3", "8:02 - 8:17 PM", "Kushivika Kengua", "Dance", "Mashup of 3 songs - 15 min", STAGE),

    # ---- Day 4 - Thursday 17 September ----------------------------------
    ("Day 4", "7:00 - 7:20 PM", "Shailaja + Group", "Dance", "Kolatam - 20 min", STAGE),
    ("Day 4", "7:20 - 7:40 PM", "Shailaja + Group", "Dance", "Kolatam - 20 min", STAGE),
    ("Day 4", "7:40 - 7:45 PM", "Snigdha Sri Sarvani", "Singing", "Singing - 5 min", STAGE),
    ("Day 4", "7:45 - 7:50 PM", "Dhruthi Ambadasu", "Singing", "Singing - 3 to 5 min", STAGE),
    ("Day 4", "7:50 - 7:51 PM", "G. Chinmayee", "Singing", "Singing - 1 min", STAGE),
    ("Day 4", "7:51 - 7:56 PM", "Akshaj", "Sloka", "Sloka Recitation - 5 min", STAGE),
    ("Day 4", "7:56 - 7:58 PM", "Meghansh Reddy", "Sloka", "Sloka Recitation - 2 min", STAGE),
    ("Day 4", "7:58 - 8:00 PM", "Eeshan", "Dance", "Western Solo - 2 min", STAGE),
    ("Day 4", "8:00 - 8:05 PM", "A. Nakshatra", "Dance", "Mashup - 5 min", STAGE),

    # ---- Day 5 - Friday 18 September ------------------------------------
    ("Day 5", "7:00 - 7:10 PM", "K Lokshith", "Dance", "Group Dance, Mashup - 10 min", STAGE),
    ("Day 5", "7:10 - 7:20 PM", "Team 1 - Devasriganesha", "Dance", "Devotional group - 10 min", STAGE),
    ("Day 5", "7:20 - 7:30 PM", "Team 2 - Shambhu Sutaya", "Dance",
     "Devotional group song - 10 min", STAGE),
    ("Day 5", "7:30 - 7:40 PM", "Team 3 - Gajannana", "Dance", "Devotional group song - 10 min", STAGE),
    ("Day 5", "7:40 - 7:50 PM", "Zumba Team - Ekadantaya Song", "Dance",
     "Devotional group - 10 min", STAGE),
    ("Day 5", "7:50 - 8:00 PM", "All Kids - Irumudi Song", "Dance", "Devotional group - 10 min", STAGE),
    ("Day 5", "8:00 - 8:05 PM", "Koushika, Nithya, Hemmani", "Dance", "Group Dance, Mashup - 5 min", STAGE),
    ("Day 5", "8:30 - 8:45 PM", "Kushivika Kengua", "Dance", "Mashup - 15 min", STAGE),
    ("Day 5", "8:45 - 8:51 PM", "Neshna Sri & Neshya Sri", "Dance", "Mashup - 6 min", STAGE),
]


class Command(BaseCommand):
    help = "Load the community Ganesh Chavithi cultural programme."

    def add_arguments(self, parser):
        parser.add_argument(
            "--replace", action="store_true", help="Delete existing events before loading"
        )

    def handle(self, *args, **options):
        if options["replace"]:
            removed = Event.objects.all().delete()[0]
            self.stdout.write(self.style.WARNING(f"Removed {removed} existing event(s)."))

        created = updated = 0
        for day, slot, performer, category, detail, place in PROGRAMME:
            _, was_created = Event.objects.update_or_create(
                day=day,
                time_slot=slot,
                title=performer,
                defaults={
                    "category": category,
                    "description": detail,
                    "location": place,
                    "is_published": True,
                },
            )
            created += was_created
            updated += not was_created

        self.stdout.write(
            self.style.SUCCESS(
                f"Programme loaded: {created} added, {updated} updated, "
                f"{Event.objects.count()} events total."
            )
        )
        for day in sorted({row[0] for row in PROGRAMME}):
            self.stdout.write(f"  {day}: {Event.objects.filter(day=day).count()} items")
