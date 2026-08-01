from django.conf import settings
from django.db import models

class ActivityLog(models.Model):

    ACTION_CHOICES = (
        ('CREATE', 'Create'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
        ('LOGIN', 'Login'),
        ('LOGOUT', 'Logout'),
        ('VIEW', 'View'),
        ('APPROVE', 'Approve'),
        ('CANCEL', 'Cancel'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    user_role = models.CharField(max_length=100, blank=True)  # snapshot of role at that time
    screen_name = models.CharField(max_length=150)
    action_type = models.CharField(max_length=20, choices=ACTION_CHOICES)
    remark = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        username = self.user.username if self.user else "System"
        return f"{username} | {self.screen_name} | {self.action_type}"
