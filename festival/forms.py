"""Forms for attendee submissions and the organiser console."""

from django import forms

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
        fields = ["title", "category", "image", "image_url", "author", "is_approved"]
        widgets = {
            "title": forms.TextInput(attrs={"class": INPUT}),
            "category": forms.Select(attrs={"class": INPUT}),
            "image": forms.ClearableFileInput(attrs={"class": FILE, "accept": "image/*"}),
            "image_url": forms.URLInput(attrs={"class": INPUT, "placeholder": "https://..."}),
            "author": forms.TextInput(attrs={"class": INPUT}),
            "is_approved": forms.CheckboxInput(attrs={"class": "w-4 h-4 accent-pink-500"}),
        }


class PhotoUploadForm(forms.ModelForm):
    """Attendee-facing upload: a photo from their device, nothing else.

    Organisers can still add pictures by URL from the console; attendees at a
    festival are holding a phone, so the file picker is the whole story.
    """

    class Meta:
        model = Photo
        fields = ["title", "category", "image", "author"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["image"].required = True
        self.fields["image"].error_messages["required"] = "Pick a photo from your device first."

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
