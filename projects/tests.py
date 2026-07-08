from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TransactionTestCase, override_settings
from django.test.client import MULTIPART_CONTENT, encode_multipart
from django.urls import reverse

from .models import AboutMeHero, Category, Project, ProjectImage, ResumeItem


TEST_STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

TEST_IMAGE_CONTENT = (
    b"GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!"
    b"\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00"
    b"\x00\x02\x02D\x01\x00;"
)


@override_settings(
    MEDIA_ROOT="/tmp/django-portfolio-test-media",
    STORAGES=TEST_STORAGES,
    SECURE_SSL_REDIRECT=False,
)
class UploadedImageDeletionTests(TransactionTestCase):
    def setUp(self):
        self.project = Project.objects.create(
            title="Test project",
            description="Description",
            technology="Django",
        )

    def tearDown(self):
        media_root = Path("/tmp/django-portfolio-test-media")
        for file_path in sorted(media_root.glob("**/*"), reverse=True):
            if file_path.is_file():
                file_path.unlink()
            elif file_path.is_dir():
                file_path.rmdir()

    def make_file(self, name):
        return SimpleUploadedFile(name, TEST_IMAGE_CONTENT, content_type="image/gif")

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

    def test_about_me_hero_file_is_deleted_when_record_is_deleted(self):
        hero = AboutMeHero.objects.create(
            image=self.make_file("about-hero.gif"),
            alt_text="Mountain trail",
        )
        file_path = hero.image.path

        hero.delete()

        self.assert_storage_file_deleted(file_path)

    def test_about_me_page_uses_uploaded_hero_image(self):
        hero = AboutMeHero.objects.create(
            image=self.make_file("about-page-hero.gif"),
            alt_text="Mountain trail",
        )

        response = self.client.get(reverse("projects:about_me"))

        self.assertContains(response, hero.image.url)
        self.assertContains(response, hero.alt_text)

    def test_admin_bulk_upload_creates_project_images(self):
        user = get_user_model().objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="password",
        )
        client = Client()
        client.force_login(user)
        url = reverse("admin:projects_project_bulk_upload_images", args=[self.project.pk])

        payload = encode_multipart(
            "BoUnDaRyStRiNg",
            {
                "images": [
                    self.make_file("first.gif"),
                    self.make_file("second.gif"),
                ],
            },
        )
        response = client.generic(
            "POST",
            url,
            payload,
            content_type=MULTIPART_CONTENT,
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.project.images.count(), 2)
        self.assertEqual(
            list(self.project.images.values_list("order", flat=True)),
            [0, 1],
        )
        self.assertTrue(self.project.images.get(order=0).uploaded_image.name)

    def test_project_image_admin_bulk_upload_creates_images_for_selected_project(self):
        user = get_user_model().objects.create_superuser(
            username="image-admin",
            email="image-admin@example.com",
            password="password",
        )
        client = Client()
        client.force_login(user)
        url = reverse("admin:projects_projectimage_bulk_upload")

        ProjectImage.objects.create(
            project=self.project,
            uploaded_image=self.make_file("existing.gif"),
            order=4,
        )
        payload = encode_multipart(
            "BoUnDaRyStRiNg",
            {
                "project": str(self.project.pk),
                "images": [
                    self.make_file("third.gif"),
                    self.make_file("fourth.gif"),
                ],
            },
        )
        response = client.generic(
            "POST",
            url,
            payload,
            content_type=MULTIPART_CONTENT,
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.project.images.count(), 3)
        self.assertEqual(
            list(self.project.images.values_list("order", flat=True)),
            [4, 5, 6],
        )
