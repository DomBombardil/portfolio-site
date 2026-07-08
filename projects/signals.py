from django.db import transaction
from django.db.models.signals import post_delete, pre_save
from django.dispatch import receiver

from .models import Project, ProjectImage, ResumeItem


IMAGE_FIELDS_BY_MODEL = {
    Project: ("cover_image",),
    ProjectImage: ("uploaded_image",),
    ResumeItem: ("uploaded_image",),
}


def delete_file_on_commit(file_field):
    if not file_field or not file_field.name:
        return

    transaction.on_commit(lambda: file_field.delete(save=False))


def delete_instance_files(instance):
    for field_name in IMAGE_FIELDS_BY_MODEL[type(instance)]:
        delete_file_on_commit(getattr(instance, field_name))


def delete_replaced_files(sender, instance):
    if not instance.pk:
        return

    field_names = IMAGE_FIELDS_BY_MODEL[sender]

    try:
        old_instance = sender.objects.only(*field_names).get(pk=instance.pk)
    except sender.DoesNotExist:
        return

    for field_name in field_names:
        old_file = getattr(old_instance, field_name)
        new_file = getattr(instance, field_name)

        if old_file and old_file.name and old_file.name != new_file.name:
            delete_file_on_commit(old_file)


@receiver(post_delete, sender=Project)
@receiver(post_delete, sender=ProjectImage)
@receiver(post_delete, sender=ResumeItem)
def delete_files_after_model_delete(sender, instance, **kwargs):
    delete_instance_files(instance)


@receiver(pre_save, sender=Project)
@receiver(pre_save, sender=ProjectImage)
@receiver(pre_save, sender=ResumeItem)
def delete_files_after_field_change(sender, instance, **kwargs):
    delete_replaced_files(sender, instance)
