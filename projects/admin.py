from django import forms
from django.contrib import admin
from django.contrib import messages
from django.db import models
from django.db.models import Max
from django.shortcuts import redirect
from django.templatetags.static import static
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.html import format_html

from .models import AboutMeHero, AboutMePP, Category, Project, ProjectImage, ResumeItem


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleImageField(forms.ImageField):
    widget = MultipleFileInput

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            return [single_file_clean(file, initial) for file in data]
        return [single_file_clean(data, initial)]


class ProjectImageBulkUploadForm(forms.Form):
    project = forms.ModelChoiceField(
        queryset=Project.objects.all(),
        required=False,
        help_text="Select the project these images belong to.",
    )
    images = MultipleImageField(
        label="Images",
        help_text="Select multiple files to add them as project detail images.",
        widget=MultipleFileInput(attrs={"multiple": True}),
    )

    def __init__(self, *args, project=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.project = project
        if project is not None:
            self.fields.pop("project")
        else:
            self.fields["project"].required = True

    def clean_project(self):
        return self.project or self.cleaned_data["project"]


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

        image = getattr(obj, "image", None)
        if image:
            if hasattr(image, "url"):
                try:
                    return image.url
                except ValueError:
                    pass
            return static(image)

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
    change_form_template = "admin/projects/project/change_form.html"
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

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "<path:object_id>/bulk-upload-images/",
                self.admin_site.admin_view(self.bulk_upload_images_view),
                name="projects_project_bulk_upload_images",
            ),
        ]
        return custom_urls + urls

    def bulk_upload_images_view(self, request, object_id):
        project = self.get_object(request, object_id)
        if project is None:
            return redirect("admin:projects_project_changelist")

        if request.method == "POST":
            form = ProjectImageBulkUploadForm(request.POST, request.FILES, project=project)
            if form.is_valid():
                images = form.cleaned_data["images"]
                create_project_images(project, images)

                self.message_user(
                    request,
                    f"Uploaded {len(images)} project image(s).",
                    messages.SUCCESS,
                )
                return redirect(
                    reverse("admin:projects_project_change", args=[project.pk])
                )
        else:
            form = ProjectImageBulkUploadForm(project=project)

        context = {
            **self.admin_site.each_context(request),
            "opts": self.model._meta,
            "original": project,
            "title": f"Bulk upload images: {project.title}",
            "form": form,
            "media": self.media + form.media,
            "change_url": reverse("admin:projects_project_change", args=[project.pk]),
        }
        return TemplateResponse(
            request,
            "admin/projects/project/bulk_upload_images.html",
            context,
        )


def create_project_images(project, images):
    max_order = project.images.aggregate(max_order=Max("order"))["max_order"]
    next_order = 0 if max_order is None else max_order + 1

    for index, image in enumerate(images):
        ProjectImage.objects.create(
            project=project,
            uploaded_image=image,
            order=next_order + index,
        )


@admin.register(ProjectImage)
class ProjectImageAdmin(ImagePreviewMixin, admin.ModelAdmin):
    change_list_template = "admin/projects/projectimage/change_list.html"
    list_display = ("project", "order", "image_preview", "uploaded_image", "image")
    list_editable = ("order",)
    list_filter = ("project",)
    search_fields = ("project__title", "image")
    ordering = ("project__position", "project__title", "order")
    readonly_fields = ("image_preview",)
    fields = ("project", "order", "uploaded_image", "image", "image_preview")

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "bulk-upload/",
                self.admin_site.admin_view(self.bulk_upload_images_view),
                name="projects_projectimage_bulk_upload",
            ),
        ]
        return custom_urls + urls

    def bulk_upload_images_view(self, request):
        if request.method == "POST":
            form = ProjectImageBulkUploadForm(request.POST, request.FILES)
            if form.is_valid():
                project = form.cleaned_data["project"]
                images = form.cleaned_data["images"]
                create_project_images(project, images)

                self.message_user(
                    request,
                    f"Uploaded {len(images)} image(s) for {project}.",
                    messages.SUCCESS,
                )
                return redirect(reverse("admin:projects_projectimage_changelist"))
        else:
            form = ProjectImageBulkUploadForm()

        context = {
            **self.admin_site.each_context(request),
            "opts": self.model._meta,
            "title": "Bulk upload project images",
            "form": form,
            "media": self.media + form.media,
            "change_url": reverse("admin:projects_projectimage_changelist"),
        }
        return TemplateResponse(
            request,
            "admin/projects/project/bulk_upload_images.html",
            context,
        )


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


@admin.register(AboutMeHero)
class AboutMeHeroAdmin(ImagePreviewMixin, admin.ModelAdmin):
    list_display = ("image_preview", "alt_text")
    fields = ("image", "alt_text", "image_preview")
    readonly_fields = ("image_preview",)

    def has_add_permission(self, request):
        return not AboutMeHero.objects.exists()
