
import uuid

from django.db import migrations, models


def generate_invoice_request_ids(apps, schema_editor):
    Invoice = apps.get_model('jobcard_app', 'Invoice')
    db_alias = schema_editor.connection.alias

    for invoice in Invoice.objects.using(db_alias).filter(
        request_id__isnull=True
    ).iterator():
        invoice.request_id = uuid.uuid4()
        invoice.save(
            using=db_alias,
            update_fields=['request_id']
        )


class Migration(migrations.Migration):

    dependencies = [
        ('jobcard_app', '0059_alter_deliverynote_vouchertype'),
    ]

    operations = [
        migrations.AddField(
            model_name='invoice',
            name='request_id',
            field=models.UUIDField(
                null=True,
                editable=False,
            ),
        ),

        migrations.RunPython(
            generate_invoice_request_ids,
            reverse_code=migrations.RunPython.noop,
        ),

        migrations.AlterField(
            model_name='invoice',
            name='request_id',
            field=models.UUIDField(
                default=uuid.uuid4,
                unique=True,
                editable=False,
            ),
        ),
    ]
