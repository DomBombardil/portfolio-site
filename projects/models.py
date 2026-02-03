from django.db import models

# Create your models here.
class Project(models.Model):
    """Class that represents a Project model."""
    title = models.CharField(max_length=100)
    description = models.TextField()
    technology = models.CharField(max_length=200)
    repository_link = models.CharField(max_length=200, null=True, blank=True)
    image = models.CharField(max_length=200)

    # NEW: Cloudinary-backed upload (because it's an ImageField)
    cover_image = models.ImageField(
        upload_to="projects/covers/",
        null=True,
        blank=True
    )

    def __str__(self):
        return f"{self.title}"

class ProjectImage(models.Model):
    """Class representing images related to a project."""
    project = models.ForeignKey(Project, related_name="images", 
                                on_delete=models.CASCADE)
    image = models.ImageField(upload_to='projects/details/')
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.project.title} image"
    
class Category(models.Model):
    """Class representing a category for resume items."""
    name = models.CharField(max_length=100, unique=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.name
    
class ResumeItem(models.Model):
    """Class representing resume items like education and employers"""
    category = models.ForeignKey(Category, related_name="resume_items",
                                 on_delete=models.CASCADE)
    title = models.CharField(max_length=100, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    image = models.CharField(max_length=200, null=True, blank=True)
    position = models.PositiveIntegerField(default=0)

    # NEW: Cloudinary-backed upload
    uploaded_image = models.ImageField(
        upload_to="resume/images/",
        null=True,
        blank=True
    )

    class Meta:
        ordering = ["position"]

    def __str__(self):
        return f"Title: {self.title} Category: {self.category}"
