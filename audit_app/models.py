from django.conf import settings
from django.db import models


class ActivityLog(models.Model):
    """
    Comprehensive audit log capturing transactional events across the Workshop ERP.
    """
    ACTION_CHOICES = (
        ('CREATE', 'Create'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
        ('STATUS_CHANGE', 'Status Change'),
        ('APPROVE', 'Approve'),
        ('CANCEL', 'Cancel'),
        ('VIEW', 'View'),
        ('LOGIN', 'Login'),
        ('LOGOUT', 'Logout'),
    )

    MODULE_CHOICES = (
        ('JOBCARD', 'Job Card Management'),
        ('INVOICE', 'Invoicing & Billing'),
        ('INVENTORY', 'Parts & Inventory'),
        ('ACCOUNTS', 'General Ledger & Accounts'),
        ('FLEET', 'Fleet / Vehicle Master'),
        ('AUTH', 'Authentication & Access'),
        ('GENERAL', 'General System'),
    )

    # 1. User tracking & Role Snapshot
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    user_username = models.CharField(max_length=150, blank=True, default='', help_text="Preserved username in case user is deleted")
    user_role = models.CharField(max_length=100, blank=True, default='', help_text="Snapshot of user role/group at time of action")

    # 2. Action & Module
    action_type = models.CharField(max_length=30, choices=ACTION_CHOICES, db_index=True)
    module = models.CharField(max_length=50, choices=MODULE_CHOICES, default='GENERAL', db_index=True)
    screen_name = models.CharField(max_length=150, blank=True, default='')

    # 3. Entity Tracking
    entity_type = models.CharField(max_length=100, blank=True, default='', db_index=True)
    entity_id = models.CharField(max_length=64, blank=True, default='', db_index=True)
    entity_reference = models.CharField(max_length=150, blank=True, default='', help_text="Human reference e.g. JC-001, INV-1002")

    # 4. Human-readable Description & Structured Diffs
    description = models.TextField(blank=True, default='', help_text="Human-readable description of the changes")
    changes_diff = models.JSONField(default=dict, blank=True, help_text="Machine-readable field changes (old vs new)")
    remark = models.TextField(blank=True, default='', help_text="Legacy remark field, mirrors description")

    # 5. Client IP and Device / Browser Metadata
    ip_address = models.GenericIPAddressField(null=True, blank=True, db_index=True)
    device_type = models.CharField(max_length=50, blank=True, default='', help_text="Desktop, Mobile, Tablet, Bot")
    browser = models.CharField(max_length=100, blank=True, default='', help_text="e.g. Chrome, Firefox, Safari")
    operating_system = models.CharField(max_length=100, blank=True, default='', help_text="e.g. Windows, Android, iOS")
    user_agent = models.TextField(blank=True, default='', help_text="Raw HTTP User-Agent string")

    # 6. Request Tracing & Timestamp
    correlation_id = models.CharField(max_length=64, blank=True, default='', db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['module', '-created_at'], name='idx_actlog_mod_time'),
            models.Index(fields=['entity_type', 'entity_id', '-created_at'], name='idx_actlog_ent_time'),
            models.Index(fields=['user', '-created_at'], name='idx_actlog_user_time'),
        ]

    def save(self, *args, **kwargs):
        # Sync remark and description for backward compatibility
        if self.description and not self.remark:
            self.remark = self.description
        elif self.remark and not self.description:
            self.description = self.remark
        
        # Snapshot username if available
        if self.user and not self.user_username:
            self.user_username = getattr(self.user, 'username', '')
            
        super().save(*args, **kwargs)

    def __str__(self):
        username = self.user_username or (self.user.username if self.user else "System")
        target = f" on {self.entity_reference}" if self.entity_reference else (f" in {self.screen_name}" if self.screen_name else "")
        return f"[{self.created_at:%Y-%m-%d %H:%M}] {username} | {self.action_type}{target}"

