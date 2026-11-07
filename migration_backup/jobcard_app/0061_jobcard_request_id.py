
import uuid

from django.db import migrations, models


def generate_jobcard_request_ids(apps, schema_editor):
    JobCard = apps.get_model('jobcard_app', 'JobCard')
    db_alias = schema_editor.connection.alias

    for job in JobCard.objects.using(db_alias).filter(
        request_id__isnull=True
    ).iterator():
        job.request_id = uuid.uuid4()
        job.save(
            using=db_alias,
            update_fields=['request_id']
        )


class Migration(migrations.Migration):

    dependencies = [
        ('jobcard_app', '0060_invoice_request_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='jobcard',
            name='request_id',
            field=models.UUIDField(
                null=True,
                editable=False
            ),
        ),

        migrations.RunPython(
            generate_jobcard_request_ids,
            reverse_code=migrations.RunPython.noop,
        ),

        migrations.AlterField(
            model_name='jobcard',
            name='request_id',
            field=models.UUIDField(
                default=uuid.uuid4,
                unique=True,
                editable=False
            ),
        ),
    ]
