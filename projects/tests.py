from pathlib import Path

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TransactionTestCase, override_settings

from .models import Category, Project, ProjectImage, ResumeItem


TEST_STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}


@override_settings(MEDIA_ROOT="/tmp/django-portfolio-test-media", STORAGES=TEST_STORAGES)
class UploadedImageDeletionTests(TransactionTestCase):
    def setUp(self):
        self.project = Project.objects.create(
            title="Test project",
            description="Description",
            technology="Django",
            image="",
        )

    def tearDown(self):
        media_root = Path("/tmp/django-portfolio-test-media")
        for file_path in sorted(media_root.glob("**/*"), reverse=True):
            if file_path.is_file():
                file_path.unlink()
            elif file_path.is_dir():
                file_path.rmdir()

    def make_file(self, name):
        return SimpleUploadedFile(name, b"test image content", content_type="image/png")

    def assert_storage_file_exists(self, field_file):
        self.assertTrue(Path(field_file.path).exists())

    def assert_storage_file_deleted(self, file_path):
        self.assertFalse(Path(file_path).exists())

    def test_project_image_file_is_deleted_when_record_is_deleted(self):
        image = ProjectImage.objects.create(
            project=self.project,
            uploaded_image=self.make_file("detail.png"),
        )
        file_path = image.uploaded_image.path
        self.assert_storage_file_exists(image.uploaded_image)

        image.delete()

        self.assert_storage_file_deleted(file_path)

    def test_project_image_file_is_deleted_when_record_is_bulk_deleted(self):
        image = ProjectImage.objects.create(
            project=self.project,
            uploaded_image=self.make_file("bulk-detail.png"),
        )
        file_path = image.uploaded_image.path

        ProjectImage.objects.filter(pk=image.pk).delete()

        self.assert_storage_file_deleted(file_path)

    def test_old_project_image_file_is_deleted_when_field_is_replaced(self):
        image = ProjectImage.objects.create(
            project=self.project,
            uploaded_image=self.make_file("old-detail.png"),
        )
        old_file_path = image.uploaded_image.path

        image.uploaded_image = self.make_file("new-detail.png")
        image.save()

        self.assert_storage_file_deleted(old_file_path)
        self.assert_storage_file_exists(image.uploaded_image)

    def test_other_uploaded_image_fields_are_deleted_when_records_are_deleted(self):
        self.project.cover_image = self.make_file("cover.png")
        self.project.save()
        cover_path = self.project.cover_image.path

        category = Category.objects.create(name="Education")
        resume_item = ResumeItem.objects.create(
            category=category,
            title="Certificate",
            uploaded_image=self.make_file("resume.png"),
        )
        resume_path = resume_item.uploaded_image.path

        self.project.delete()
        resume_item.delete()

        self.assert_storage_file_deleted(cover_path)
        self.assert_storage_file_deleted(resume_path)
