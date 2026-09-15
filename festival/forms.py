"""Forms for attendee submissions and the organiser console."""

from pathlib import Path

from django import forms
from django.conf import settings

from .models import Event, Feedback, Photo, Poll, PollOption

INPUT = (
    "w-full bg-fest-cardLight border border-white/10 rounded-xl px-3 py-2 text-sm "
    "text-white placeholder-gray-500 focus:outline-none focus:border-fest-accent"
)
AREA = INPUT + " leading-relaxed"
FILE = (
    "w-full text-xs text-gray-300 file:mr-3 file:py-2 file:px-3 file:rounded-lg "
    "file:border-0 file:bg-fest-accent file:text-white file:font-bold file:text-xs"
)


class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = [
            "title",
            "day",
            "time_slot",
            "location",
            "category",
            "description",
            "image",
            "image_url",
            "is_published",
        ]
        widgets = {
            "title": forms.TextInput(attrs={"class": INPUT, "placeholder": "Cyber Beats Live"}),
            "day": forms.Select(attrs={"class": INPUT}),
            "time_slot": forms.TextInput(attrs={"class": INPUT, "placeholder": "19:00 - 21:00"}),
            "location": forms.TextInput(attrs={"class": INPUT, "placeholder": "Main Stage"}),
            "category": forms.Select(attrs={"class": INPUT}),
            "description": forms.Textarea(attrs={"class": AREA, "rows": 3}),
            "image": forms.ClearableFileInput(attrs={"class": FILE, "accept": "image/*"}),
            "image_url": forms.URLInput(attrs={"class": INPUT, "placeholder": "https://..."}),
            "is_published": forms.CheckboxInput(
                attrs={"class": "w-4 h-4 accent-pink-500 rounded"}
            ),
        }

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get("image") and not cleaned.get("image_url"):
            self.add_error("image_url", "Upload an image file or paste an image URL.")
        return cleaned


class PhotoForm(forms.ModelForm):
    """Used by the console; attendees get PhotoUploadForm below."""

    class Meta:
        model = Photo
        fields = ["title", "category", "image", "video", "image_url", "author", "is_approved"]
        widgets = {
            "title": forms.TextInput(attrs={"class": INPUT}),
            "category": forms.Select(attrs={"class": INPUT}),
            "image": forms.ClearableFileInput(attrs={"class": FILE, "accept": "image/*"}),
            "video": forms.ClearableFileInput(attrs={"class": FILE, "accept": "video/*"}),
            "image_url": forms.URLInput(attrs={"class": INPUT, "placeholder": "https://..."}),
            "author": forms.TextInput(attrs={"class": INPUT}),
            "is_approved": forms.CheckboxInput(attrs={"class": "w-4 h-4 accent-pink-500"}),
        }


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".heic", ".heif"}
VIDEO_EXTENSIONS = {".mp4", ".webm", ".mov", ".m4v"}


class PhotoUploadForm(forms.ModelForm):
    """Attendee upload: one file picker that takes a photo or a short clip.

    A single field is the whole interaction on a phone - the file is routed to
    the image or video column by its type. Organisers can still add pictures by
    URL from the console.
    """

    media = forms.FileField(
        label="Photo or video",
        error_messages={"required": "Pick a photo or video from your device first."},
    )

    class Meta:
        model = Photo
        fields = ["title", "category", "author"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # The name box is optional on the modal; clean_author supplies the
        # default. Without this, leaving it blank fails the upload outright.
        self.fields["author"].required = False

    def clean_media(self):
        upload = self.cleaned_data["media"]
        extension = Path(upload.name).suffix.lower()

        if extension in VIDEO_EXTENSIONS:
            limit = getattr(settings, "FEST_MAX_VIDEO_MB", 25)
            if upload.size > limit * 1024 * 1024:
                raise forms.ValidationError(
                    f"That clip is {upload.size // (1024 * 1024)} MB. Keep videos under {limit} MB."
                )
            self.media_kind = "video"
            return upload

        if extension in IMAGE_EXTENSIONS:
            limit = getattr(settings, "FEST_MAX_IMAGE_MB", 10)
            if upload.size > limit * 1024 * 1024:
                raise forms.ValidationError(f"That photo is over {limit} MB. Try a smaller one.")
            self.media_kind = "image"
            return upload

        raise forms.ValidationError(
            "Pick a photo (jpg, png, heic) or a short video (mp4, webm, mov)."
        )

    def save(self, commit=True):
        item = super().save(commit=False)
        upload = self.cleaned_data["media"]
        if self.media_kind == "video":
            item.video = upload
        else:
            item.image = upload
        if commit:
            item.save()
        return item

    def clean_title(self):
        return self.cleaned_data["title"].strip() or "Festival Capture"

    def clean_author(self):
        return self.cleaned_data["author"].strip() or "Festival Fan"


class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ["rating", "category", "comment", "contact", "festival_day"]

    def clean_rating(self):
        rating = self.cleaned_data["rating"]
        if not 1 <= rating <= 5:
            raise forms.ValidationError("Rating must be between 1 and 5.")
        return rating


class PollForm(forms.Form):
    """Creates a poll plus two to four options in one step."""

    question = forms.CharField(
        max_length=200,
        widget=forms.TextInput(
            attrs={"class": INPUT, "placeholder": "e.g. Best Stage Visuals of Night 1?"}
        ),
    )
    option_1 = forms.CharField(
        max_length=120, widget=forms.TextInput(attrs={"class": INPUT, "placeholder": "Option A"})
    )
    option_2 = forms.CharField(
        max_length=120, widget=forms.TextInput(attrs={"class": INPUT, "placeholder": "Option B"})
    )
    option_3 = forms.CharField(
        max_length=120,
        required=False,
        widget=forms.TextInput(attrs={"class": INPUT, "placeholder": "Option C (optional)"}),
    )
    option_4 = forms.CharField(
        max_length=120,
        required=False,
        widget=forms.TextInput(attrs={"class": INPUT, "placeholder": "Option D (optional)"}),
    )
    is_active = forms.BooleanField(
        required=False, initial=True, widget=forms.CheckboxInput(attrs={"class": "w-4 h-4 accent-pink-500"})
    )

    def save(self):
        poll = Poll.objects.create(
            question=self.cleaned_data["question"],
            is_active=self.cleaned_data.get("is_active", True),
        )
        for index in range(1, 5):
            text = (self.cleaned_data.get(f"option_{index}") or "").strip()
            if text:
                PollOption.objects.create(poll=poll, text=text, position=index)
        return poll
