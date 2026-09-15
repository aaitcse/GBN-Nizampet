"""Domain models for the GBN festival companion app."""

from django.db import models
from django.utils import timezone


class Event(models.Model):
    """A single scheduled item on the festival programme."""

    DAY_CHOICES = [
        ("Day 1", "Day 1 (Fri)"),
        ("Day 2", "Day 2 (Sat)"),
        ("Day 3", "Day 3 (Sun)"),
    ]
    CATEGORY_CHOICES = [
        ("Music", "Music"),
        ("Food", "Food"),
        ("Show", "Show"),
        ("Workshop", "Workshop"),
        ("Sports", "Sports"),
        ("Other", "Other"),
    ]

    title = models.CharField(max_length=160)
    day = models.CharField(max_length=10, choices=DAY_CHOICES, default="Day 1")
    time_slot = models.CharField(max_length=60, help_text="e.g. 19:00 - 21:00")
    location = models.CharField(max_length=120, help_text="Stage or venue name")
    category = models.CharField(max_length=40, choices=CATEGORY_CHOICES, default="Music")
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to="events/", blank=True, null=True)
    image_url = models.URLField(blank=True, help_text="Used when no image file is uploaded")
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["day", "time_slot", "title"]

    def __str__(self):
        return f"{self.title} ({self.day})"

    @property
    def display_image(self):
        if self.image:
            return self.image.url
        return self.image_url or (
            "https://images.unsplash.com/photo-1470225620780-dba8ba36b745"
            "?auto=format&fit=crop&w=400&q=80"
        )

    @property
    def bookmark_count(self):
        return self.bookmarks.count()


class Bookmark(models.Model):
    """An attendee saving an event to their personal agenda (session scoped)."""

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="bookmarks")
    session_key = models.CharField(max_length=64, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("event", "session_key")

    def __str__(self):
        return f"{self.session_key[:8]} -> {self.event.title}"


class Photo(models.Model):
    """A gallery image, either curated by the crew or submitted by an attendee."""

    CATEGORY_CHOICES = [
        ("Stage", "Main Stage"),
        ("Crowd", "Crowd Vibes"),
        ("Night", "Night Lights"),
    ]

    title = models.CharField(max_length=160)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default="Stage")
    image = models.ImageField(upload_to="gallery/", blank=True, null=True)
    image_url = models.URLField(blank=True)
    author = models.CharField(max_length=80, default="Festival Fan")
    is_approved = models.BooleanField(default=False)
    likes = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    @property
    def display_image(self):
        if self.image:
            return self.image.url
        return self.image_url or (
            "https://images.unsplash.com/photo-1492684223066-81342ee5ff30"
            "?auto=format&fit=crop&w=600&q=80"
        )


class PhotoLike(models.Model):
    """One like per session per photo."""

    photo = models.ForeignKey(Photo, on_delete=models.CASCADE, related_name="photo_likes")
    session_key = models.CharField(max_length=64, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("photo", "session_key")


class Poll(models.Model):
    """A live crowd poll published from the admin console."""

    question = models.CharField(max_length=200)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.question

    @property
    def total_votes(self):
        return sum(option.votes for option in self.options.all())


class PollOption(models.Model):
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name="options")
    text = models.CharField(max_length=120)
    votes = models.PositiveIntegerField(default=0)
    position = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["position", "id"]

    def __str__(self):
        return f"{self.text} ({self.votes})"

    def percentage(self, total):
        if not total:
            return 0
        return round(self.votes * 100 / total)


class Vote(models.Model):
    """Records who voted so a session cannot vote twice on the same poll."""

    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name="votes")
    option = models.ForeignKey(PollOption, on_delete=models.CASCADE, related_name="vote_records")
    session_key = models.CharField(max_length=64, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("poll", "session_key")


class Feedback(models.Model):
    """Attendee feedback and suggestions landing in the organiser inbox."""

    CATEGORY_CHOICES = [
        ("Sound & Stage", "Sound & Stage Quality"),
        ("Food & Drinks", "Food & Drinks Vendors"),
        ("Facilities & Cleanliness", "Facilities & Cleanliness"),
        ("Security & Safety", "Security & Safety"),
        ("General Suggestion", "General Suggestion"),
    ]

    rating = models.PositiveSmallIntegerField(default=5)
    category = models.CharField(max_length=40, choices=CATEGORY_CHOICES, default="General Suggestion")
    comment = models.TextField()
    contact = models.CharField(max_length=120, blank=True)
    festival_day = models.CharField(max_length=10, blank=True)
    is_resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "feedback"

    def __str__(self):
        return f"{self.get_category_display()} - {self.rating}star"

    @property
    def stars(self):
        return range(self.rating)

    @property
    def empty_stars(self):
        return range(5 - self.rating)

    @property
    def age(self):
        delta = timezone.now() - self.created_at
        if delta.days:
            return f"{delta.days}d ago"
        hours = delta.seconds // 3600
        if hours:
            return f"{hours}h ago"
        return f"{max(delta.seconds // 60, 1)}m ago"
