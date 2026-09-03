"""
Ticket data models
"""
import uuid
from django.db import models
from django.utils import timezone


class TicketRecord(models.Model):
    """Ticket record (for auditing and querying)"""
    
    STATUS_CHOICES = [
        (0, 'Unused'),
        (1, 'Used'),
        (2, 'Expired'),
        (3, 'Revoked'),
    ]
    
    ACTION_CHOICES = [
        ('execute_command', 'Execute command'),
        ('upload_file', 'Upload file'),
        ('download_file', 'Download file'),
        ('maintenance', 'Maintenance operation'),
        ('*', 'All operations'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ticket_id = models.CharField(max_length=128, unique=True, verbose_name="Ticket ID", db_index=True)
    host_uuid = models.UUIDField(verbose_name="Host UUID", db_index=True)
    action = models.CharField(max_length=50, choices=ACTION_CHOICES, default='execute_command', verbose_name="Allowed action")
    command = models.CharField(max_length=500, null=True, blank=True, verbose_name="Allowed command to execute")
    status = models.IntegerField(choices=STATUS_CHOICES, default=0, verbose_name="Status", db_index=True)
    nonce = models.CharField(max_length=128, unique=True, verbose_name="Nonce", db_index=True)
    expires_at = models.DateTimeField(verbose_name="Expiration time")
    used_at = models.DateTimeField(null=True, blank=True, verbose_name="Used at")
    used_by = models.CharField(max_length=100, null=True, blank=True, verbose_name="Used by IP")
    metadata = models.JSONField(default=dict, blank=True, verbose_name="Metadata")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created at")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated at")
    
    def __str__(self):
        return f"{self.ticket_id} - {self.get_status_display()}"
    
    class Meta:
        verbose_name = "Ticket record"
        verbose_name_plural = verbose_name
        db_table = "ticket_record"
        ordering = ['-created_at']


class AuditLog(models.Model):
    """Audit log"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ticket_id = models.CharField(max_length=128, verbose_name="Ticket ID", db_index=True)
    event = models.CharField(max_length=50, verbose_name="Event type", db_index=True, 
                            help_text="generated/verified/revoked")
    host_uuid = models.UUIDField(verbose_name="Host UUID")
    client_ip = models.CharField(max_length=100, null=True, blank=True, verbose_name="Client IP")
    result = models.CharField(max_length=20, verbose_name="Result", 
                             help_text="success/failed")
    detail = models.JSONField(default=dict, blank=True, verbose_name="Detail")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created at")
    
    def __str__(self):
        return f"{self.ticket_id} - {self.event} - {self.result}"
    
    class Meta:
        verbose_name = "Audit log"
        verbose_name_plural = verbose_name
        db_table = "audit_log"
        ordering = ['-created_at']