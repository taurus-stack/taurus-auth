"""
Ticket serializers
"""
from rest_framework import serializers
from .models import TicketRecord, AuditLog


class GenerateTicketRequestSerializer(serializers.Serializer):
    """Generate ticket request serializer"""
    host_uuid = serializers.UUIDField(required=True, help_text="Host UUID")
    action = serializers.ChoiceField(
        choices=TicketRecord.ACTION_CHOICES,
        default='execute_command',
        help_text="Allowed action"
    )
    command = serializers.CharField(
        max_length=500,
        required=False,
        allow_blank=True,
        allow_null=True,
        help_text="Allowed command to execute (optional)"
    )
    expires_minutes = serializers.IntegerField(
        min_value=1,
        max_value=60,
        default=5,
        help_text="Expiration time in minutes"
    )
    metadata = serializers.JSONField(
        required=False,
        default=dict,
        help_text="Metadata"
    )


class GenerateTicketResponseSerializer(serializers.Serializer):
    """Generate ticket response serializer"""
    ticket = serializers.CharField(help_text="Ticket string")
    ticket_id = serializers.CharField(help_text="Ticket ID")
    nonce = serializers.CharField(help_text="Nonce")
    expires_at = serializers.DateTimeField(help_text="Expiration time")
    host_uuid = serializers.UUIDField(help_text="Host UUID")
    action = serializers.CharField(help_text="Allowed action")
    command = serializers.CharField(allow_null=True, help_text="Allowed command to execute")


class VerifyTicketRequestSerializer(serializers.Serializer):
    """Verify ticket request serializer"""
    ticket = serializers.CharField(required=True, help_text="Ticket string")
    client_ip = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True,
        allow_null=True,
        help_text="Client IP"
    )


class VerifyTicketResponseSerializer(serializers.Serializer):
    """Verify ticket response serializer"""
    valid = serializers.BooleanField(help_text="Whether valid")
    host_uuid = serializers.UUIDField(allow_null=True, help_text="Host UUID")
    action = serializers.CharField(allow_null=True, help_text="Allowed action")
    command = serializers.CharField(allow_null=True, help_text="Allowed command to execute")
    reason = serializers.CharField(allow_null=True, help_text="Failure reason")


class RevokeTicketRequestSerializer(serializers.Serializer):
    """Revoke ticket request serializer"""
    reason = serializers.CharField(
        max_length=255,
        required=False,
        allow_blank=True,
        allow_null=True,
        help_text="Revocation reason"
    )


class TicketRecordSerializer(serializers.ModelSerializer):
    """Ticket record serializer"""
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    action_display = serializers.CharField(source='get_action_display', read_only=True)
    
    class Meta:
        model = TicketRecord
        fields = '__all__'
        read_only_fields = ['id', 'ticket_id', 'created_at', 'updated_at']


class AuditLogSerializer(serializers.ModelSerializer):
    """Audit log serializer"""
    
    class Meta:
        model = AuditLog
        fields = '__all__'
        read_only_fields = ['id', 'created_at']