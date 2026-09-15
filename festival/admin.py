from django.conf import settings
from django.contrib import admin

from .models import (
    Bookmark,
    Event,
    Feedback,
    PageView,
    Photo,
    PhotoLike,
    Poll,
    PollOption,
    TshirtOrder,
    Vote,
)


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("title", "day", "time_slot", "location", "category", "is_published")
    list_filter = ("day", "category", "is_published")
    search_fields = ("title", "location", "description")
    list_editable = ("is_published",)


@admin.register(Photo)
class PhotoAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "author", "is_approved", "likes", "created_at")
    list_filter = ("category", "is_approved")
    search_fields = ("title", "author")
    list_editable = ("is_approved",)
    actions = ["approve_photos", "hide_photos"]

    @admin.action(description="Approve selected photos")
    def approve_photos(self, request, queryset):
        queryset.update(is_approved=True)

    @admin.action(description="Hide selected photos")
    def hide_photos(self, request, queryset):
        queryset.update(is_approved=False)


class PollOptionInline(admin.TabularInline):
    model = PollOption
    extra = 2


@admin.register(Poll)
class PollAdmin(admin.ModelAdmin):
    list_display = ("question", "is_active", "total_votes", "created_at")
    list_filter = ("is_active",)
    inlines = [PollOptionInline]


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ("category", "rating", "short_comment", "contact", "is_resolved", "created_at")
    list_filter = ("category", "rating", "is_resolved")
    search_fields = ("comment", "contact")

    @admin.display(description="Comment")
    def short_comment(self, obj):
        return obj.comment[:60] + ("..." if len(obj.comment) > 60 else "")


@admin.register(TshirtOrder)
class TshirtOrderAdmin(admin.ModelAdmin):
    list_display = ("flat_number", "name", "mobile", "size", "quantity", "is_collected", "created_at")
    list_filter = ("size", "is_collected")
    search_fields = ("flat_number", "name", "mobile")
    list_editable = ("is_collected",)


@admin.register(PageView)
class PageViewAdmin(admin.ModelAdmin):
    list_display = ("created_at", "tab", "session_key")
    list_filter = ("tab", "created_at")
    date_hierarchy = "created_at"


admin.site.register([Bookmark, PhotoLike, Vote])
admin.site.site_header = f"{settings.FEST_BRAND} Festival Administration"
admin.site.site_title = settings.FEST_BRAND
admin.site.index_title = "Festival data"
