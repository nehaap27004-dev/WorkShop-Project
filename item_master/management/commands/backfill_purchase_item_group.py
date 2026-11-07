# management/commands/backfill_purchase_item_group.py
from django.core.management.base import BaseCommand
from django.db import transaction
from item_master.models import PurchaseDetail

class Command(BaseCommand):
    help = "Backfill PurchaseDetail.item_group from the related Item's group, where missing."

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true')

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        qs = PurchaseDetail.objects.filter(
            item_group__isnull=True,
            item_name__isnull=False,
        ).select_related('item_name')

        total = qs.count()
        updated, skipped = 0, 0

        self.stdout.write(f"Found {total} purchase items missing item_group.")

        with transaction.atomic():
            for detail in qs.iterator():
                group = getattr(detail.item_name, 'item_group_id', None)  # ← confirm this field name on Item
                if group:
                    detail.item_group_id = group
                    if not dry_run:
                        detail.save(update_fields=['item_group'])
                    updated += 1
                else:
                    skipped += 1

            if dry_run:
                self.stdout.write(self.style.WARNING("DRY RUN — rolling back."))
                transaction.set_rollback(True)

        self.stdout.write(self.style.SUCCESS(
            f"Updated: {updated}, Skipped (item has no group): {skipped}"
        ))