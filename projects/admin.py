from django import forms
from django.contrib import admin
from django.db import models
from django.templatetags.static import static
from django.utils.html import format_html

from .models import AboutMePP, Category, Project, ProjectImage, ResumeItem


class LargeTextArea(forms.Textarea):
    def __init__(self, attrs=None):
        default_attrs = {"rows": 8, "style": "width: 90%; max-width: 900px;"}
        if attrs:
            default_attrs.update(attrs)
        super().__init__(default_attrs)


class ImagePreviewMixin:
    @admin.display(description="Preview")
    def image_preview(self, obj):
        image_url = self._image_url(obj)
        if not image_url:
            return "No image"

        return format_html(
            '<img src="{}" style="height: 80px; width: 120px; object-fit: cover; border-radius: 6px;" />',
            image_url,
        )

    def _image_url(self, obj):
        uploaded_image = getattr(obj, "uploaded_image", None) or getattr(obj, "cover_image", None)
        if uploaded_image:
            try:
                return uploaded_image.url
            except ValueError:
                pass

        static_image = getattr(obj, "image", None)
        if static_image:
            return static(static_image)

        return None


class ProjectImageInline(ImagePreviewMixin, admin.TabularInline):
    model = ProjectImage
    fields = ("order", "uploaded_image", "image", "image_preview")
    readonly_fields = ("image_preview",)
    extra = 1
    ordering = ("order",)
    verbose_name = "project detail image"
    verbose_name_plural = "Project detail images"


@admin.register(Project)
class ProjectAdmin(ImagePreviewMixin, admin.ModelAdmin):
    list_display = ("position", "image_preview", "title", "technology", "repository_link")
    list_display_links = ("title",)
    list_editable = ("position",)
    ordering = ("position", "id")
    search_fields = ("title", "description", "technology")
    inlines = (ProjectImageInline,)
    save_on_top = True
    fieldsets = (
        ("Main content", {
            "fields": ("title", "description", "technology", "position"),
        }),
        ("Images", {
            "fields": ("cover_image", "image", "image_preview"),
            "description": "Use cover image for new uploads. Keep image only for old static image paths.",
        }),
        ("Links", {
            "fields": ("repository_link",),
        }),
    )
    readonly_fields = ("image_preview",)
    formfield_overrides = {
        models.TextField: {"widget": LargeTextArea},
    }


@admin.register(ProjectImage)
class ProjectImageAdmin(ImagePreviewMixin, admin.ModelAdmin):
    list_display = ("project", "order", "image_preview", "uploaded_image", "image")
    list_editable = ("order",)
    list_filter = ("project",)
    search_fields = ("project__title", "image")
    ordering = ("project__position", "project__title", "order")
    readonly_fields = ("image_preview",)
    fields = ("project", "order", "uploaded_image", "image", "image_preview")


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("order", "name")
    list_display_links = ("name",)
    list_editable = ("order",)
    ordering = ("order",)
    search_fields = ("name",)


@admin.register(ResumeItem)
class ResumeItemAdmin(ImagePreviewMixin, admin.ModelAdmin):
    list_display = ("category", "position", "title", "date_range", "image_preview")
    list_display_links = ("title",)
    list_editable = ("position",)
    list_filter = ("category",)
    search_fields = ("title", "description", "category__name")
    ordering = ("category__order", "position", "id")
    save_on_top = True
    fieldsets = (
        ("Main content", {
            "fields": ("category", "title", "description", "position"),
        }),
        ("Dates", {
            "fields": ("start_date", "end_date"),
        }),
        ("Images", {
            "fields": ("uploaded_image", "image", "image_preview"),
            "description": "Use uploaded image for new files. Keep image only for old static image paths.",
        }),
    )
    readonly_fields = ("image_preview",)
    formfield_overrides = {
        models.TextField: {"widget": LargeTextArea},
    }

    @admin.display(description="Dates")
    def date_range(self, obj):
        if obj.start_date and obj.end_date:
            return f"{obj.start_date:%d.%m.%Y} - {obj.end_date:%d.%m.%Y}"
        if obj.start_date:
            return f"{obj.start_date:%d.%m.%Y} - Present"
        if obj.end_date:
            return f"Until {obj.end_date:%d.%m.%Y}"
        return "-"


@admin.register(AboutMePP)
class AboutMePPAdmin(admin.ModelAdmin):
    list_display = ("short_description",)
    formfield_overrides = {
        models.TextField: {"widget": LargeTextArea},
    }

    @admin.display(description="Description")
    def short_description(self, obj):
        if not obj.description:
            return "Empty"
        return obj.description[:120]
