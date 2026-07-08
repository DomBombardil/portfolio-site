import hashlib

from django.conf import settings
from django.contrib import messages
from django.core.cache import cache
from django.core.mail import EmailMessage
from django.db.models import Prefetch, Q
from django.shortcuts import redirect, render

from .forms import ContactForm
from .models import AboutMeHero, AboutMePP, Project, ProjectImage, ResumeItem


def _client_ip(request):
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "unknown")


def _contact_rate_limited(request):
    limit = getattr(settings, "CONTACT_RATE_LIMIT_COUNT", 5)
    window_seconds = getattr(settings, "CONTACT_RATE_LIMIT_SECONDS", 600)
    ip_hash = hashlib.sha256(_client_ip(request).encode("utf-8")).hexdigest()
    cache_key = f"contact-rate:{ip_hash}"
    current_count = cache.get(cache_key, 0)

    if current_count >= limit:
        return True

    if not cache.add(cache_key, 1, timeout=window_seconds):
        try:
            cache.incr(cache_key)
        except ValueError:
            cache.set(cache_key, 1, timeout=window_seconds)

    return False


def all_projects(request):
    project_images = ProjectImage.objects.filter(
        uploaded_image__isnull=False,
    ).exclude(uploaded_image="").order_by("order", "id")
    projects = (
        Project.objects
        .prefetch_related(Prefetch("images", queryset=project_images, to_attr="card_images"))
        .order_by("position", "id")
    )
    return render(request, "projects/all_projects.html", {"projects": projects})


def project_detail(request, pk):
    project = Project.objects.get(pk=pk)
    project_img = (
        ProjectImage.objects
        .filter(project=project, uploaded_image__isnull=False)
        .exclude(uploaded_image="")
        .order_by("order", "id")
    )
    return render(request, "projects/detail.html", {"project": project, "project_img": project_img})


def index(request):
    project_images = ProjectImage.objects.filter(
        uploaded_image__isnull=False,
    ).exclude(uploaded_image="").order_by("order", "id")
    projects = (
        Project.objects
        .prefetch_related(Prefetch("images", queryset=project_images, to_attr="card_images"))
        .filter(
            (Q(cover_image__isnull=False) & ~Q(cover_image="")) |
            (Q(images__uploaded_image__isnull=False) & ~Q(images__uploaded_image=""))
        )
        .distinct()
        .order_by("position", "id")
    )
    return render(request, "projects/index.html", {"projects": projects})


def resume(request):
    resume_items = (
        ResumeItem.objects
        .exclude(category__name__in=["Programming certifications", "Language certifications","Formal certification"])  
        .select_related("category")              
        .order_by("category__order", "position", "id") 
    )
    return render(request, "projects/resume.html", {"resume_items": resume_items})


def certificates(request):
    programming_certs = (
        ResumeItem.objects
        .filter(category__name="Programming certifications")   
        .select_related("category")
        .order_by("position", "id")
    )
    language_certs = (
        ResumeItem.objects
        .filter(category__name="Language certifications")   
        .select_related("category")
        .order_by("position", "id")
    )
    formal_certs = (
        ResumeItem.objects
        .filter(category__name="Formal certification")
        .select_related("category")
        .order_by("position", "id")
    )
        
    context = {"programming_certs": programming_certs, 
               "language_certs": language_certs,
               "formal_certs": formal_certs,
               }
    return render(request, "projects/certificates.html", context)


def about_me(request):
    resume_item = ResumeItem.objects.all().select_related("category")
    pp_description = AboutMePP.objects.first()
    hero = AboutMeHero.objects.first()
    return render(
        request,
        "projects/about_me.html",
        {
            "resume_item": resume_item,
            "pp_description": pp_description,
            "hero": hero,
        },
    )


def contact(request):
    if request.method == "POST":
        if _contact_rate_limited(request):
            messages.error(
                request,
                "Too many messages sent recently. Please try again later.",
            )
            return redirect("projects:contact")

        form = ContactForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]
            subject = form.cleaned_data["subject"]
            message = form.cleaned_data["message"]
            body = (
                f"New portfolio contact message\n\n"
                f"From: {email}\n"
                f"Subject: {subject}\n\n"
                f"{message}"
            )
            email_message = EmailMessage(
                subject=f"Portfolio contact: {subject}",
                body=body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[settings.CONTACT_EMAIL],
                reply_to=[email],
            )

            try:
                email_message.send(fail_silently=False)
            except Exception:
                messages.error(
                    request,
                    "Your message could not be sent right now. Please try again later.",
                )
            else:
                messages.success(request, "Your message has been sent.")
                return redirect("projects:contact")
    else:
        form = ContactForm()

    return render(request, "projects/contact.html", {"form": form})
