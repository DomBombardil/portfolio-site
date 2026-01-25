from django.shortcuts import render
from .models import Project, ProjectImage, ResumeItem


def all_projects(request):
    projects = Project.objects.all()
    return render(request, "projects/all_projects.html", {"projects": projects})


def project_detail(request, pk):
    project = Project.objects.get(pk=pk)
    project_img = ProjectImage.objects.filter(project=project)
    return render(request, "projects/detail.html", {"project": project, "project_img": project_img})


def index(request):
    projects = Project.objects.all()
    return render(request, "projects/index.html", {"projects": projects})


def resume(request):
    resume_items = (
        ResumeItem.objects
        .exclude(category__name="Certificates")  
        .select_related("category")              
        .order_by("category__order", "position", "id") 
    )
    return render(request, "projects/resume.html", {"resume_items": resume_items})


def certificates(request):
    resume_items = (
        ResumeItem.objects
        .filter(category__name="Certificates")   
        .select_related("category")
        .order_by("-position", "id")
    )
    return render(request, "projects/certificates.html", {"resume_items": resume_items})


def about_me(request):
    resume_item = ResumeItem.objects.all().select_related("category")
    return render(request, "projects/about_me.html", {"resume_item": resume_item})
