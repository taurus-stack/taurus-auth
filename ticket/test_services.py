"""
ticket/services.py TicketService unit tests

Test contents:
1. generate_ticket - Generate ticket
2. verify_ticket - Verify ticket
3. revoke_ticket - Revoke ticket
4. Expired ticket handling
5. Reuse protection

Uses mock to isolate database and cache dependencies
"""
import uuid
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, PropertyMock

import pymacaroons
import pytest
from django.test import TestCase
from django.utils import timezone

from ticket.services import TicketService
from ticket.models import TicketRecord


class TicketServiceGenerateTest(TestCase):
    def setUp(self):
        self.service = TicketService()
        self.host_uuid = str(uuid.uuid4())

    @patch("ticket.services.cache")
    @patch("ticket.services.AuditLog")
    @patch("ticket.services.TicketRecord.objects")
    def test_generate_returns_ticket_info(self, mock_objects, mock_audit_objects, mock_cache):
        mock_record = MagicMock()
        mock_record.ticket_id = "ticket_test123"
        mock_record.host_uuid = uuid.UUID(self.host_uuid)
        mock_record.action = "execute_command"
        mock_record.command = None
        mock_record.nonce = "test-nonce"
        mock_record.expires_at = timezone.now() + timedelta(minutes=5)
        mock_objects.create.return_value = mock_record
        mock_audit_objects.create.return_value = MagicMock()

        result = self.service.generate_ticket(
            host_uuid=self.host_uuid,
            action="execute_command",
        )
        assert "ticket" in result
        assert "ticket_id" in result
        assert "nonce" in result
        assert "expires_at" in result
        assert result["host_uuid"] == self.host_uuid
        assert result["action"] == "execute_command"

    @patch("ticket.services.cache")
    @patch("ticket.services.AuditLog")
    @patch("ticket.services.TicketRecord.objects")
    def test_generate_creates_db_record(self, mock_objects, mock_audit_objects, mock_cache):
        mock_objects.create.return_value = MagicMock()
        mock_audit_objects.create.return_value = MagicMock()

        result = self.service.generate_ticket(
            host_uuid=self.host_uuid,
            action="execute_command",
        )
        mock_objects.create.assert_called_once()
        call_kwargs = mock_objects.create.call_args[1]
        assert call_kwargs["host_uuid"] == self.host_uuid
        assert call_kwargs["action"] == "execute_command"

    @patch("ticket.services.cache")
    @patch("ticket.services.AuditLog.objects")
    @patch("ticket.services.TicketRecord.objects")
    def test_generate_creates_audit_log(self, mock_objects, mock_audit_objects, mock_cache):
        mock_objects.create.return_value = MagicMock()
        mock_audit_objects.create.return_value = MagicMock()

        result = self.service.generate_ticket(
            host_uuid=self.host_uuid,
            action="execute_command",
        )
        mock_audit_objects.create.assert_called_once()
        call_kwargs = mock_audit_objects.create.call_args[1]
        assert call_kwargs["event"] == "generated"
        assert call_kwargs["result"] == "success"

    @patch("ticket.services.cache")
    @patch("ticket.services.AuditLog")
    @patch("ticket.services.TicketRecord.objects")
    def test_generate_with_command(self, mock_objects, mock_audit_objects, mock_cache):
        mock_objects.create.return_value = MagicMock()
        mock_audit_objects.create.return_value = MagicMock()

        result = self.service.generate_ticket(
            host_uuid=self.host_uuid,
            action="execute_command",
            command="ls -la",
        )
        assert result["command"] == "ls -la"
        call_kwargs = mock_objects.create.call_args[1]
        assert call_kwargs["command"] == "ls -la"

    @patch("ticket.services.cache")
    @patch("ticket.services.AuditLog")
    @patch("ticket.services.TicketRecord.objects")
    def test_generate_with_custom_expiry(self, mock_objects, mock_audit_objects, mock_cache):
        mock_objects.create.return_value = MagicMock()
        mock_audit_objects.create.return_value = MagicMock()

        result = self.service.generate_ticket(
            host_uuid=self.host_uuid,
            action="execute_command",
            expires_minutes=10,
        )
        call_kwargs = mock_objects.create.call_args[1]
        delta = call_kwargs["expires_at"] - timezone.now()
        assert 9 * 60 <= delta.total_seconds() <= 11 * 60

    @patch("ticket.services.cache")
    @patch("ticket.services.AuditLog")
    @patch("ticket.services.TicketRecord.objects")
    def test_generate_expiry_capped_at_max(self, mock_objects, mock_audit_objects, mock_cache):
        mock_objects.create.return_value = MagicMock()
        mock_audit_objects.create.return_value = MagicMock()

        result = self.service.generate_ticket(
            host_uuid=self.host_uuid,
            action="execute_command",
            expires_minutes=9999,
        )
        call_kwargs = mock_objects.create.call_args[1]
        delta = call_kwargs["expires_at"] - timezone.now()
        assert delta.total_seconds() <= 61 * 60

    @patch("ticket.services.cache")
    @patch("ticket.services.AuditLog")
    @patch("ticket.services.TicketRecord.objects")
    def test_generate_with_metadata(self, mock_objects, mock_audit_objects, mock_cache):
        mock_objects.create.return_value = MagicMock()
        mock_audit_objects.create.return_value = MagicMock()

        result = self.service.generate_ticket(
            host_uuid=self.host_uuid,
            action="execute_command",
            metadata={"source": "test"},
        )
        call_kwargs = mock_objects.create.call_args[1]
        assert call_kwargs["metadata"] == {"source": "test"}


class TicketServiceVerifyTest(TestCase):
    def setUp(self):
        self.service = TicketService()
        self.host_uuid = str(uuid.uuid4())

    def _create_macaroon(self, ticket_id, host_uuid, action, nonce, expires_at):
        macaroon = pymacaroons.Macaroon(
            location="taurus-auth",
            identifier=ticket_id.encode(),
            key=self.service.root_key,
        )
        macaroon.add_first_party_caveat(f"time < {expires_at.isoformat()}")
        macaroon.add_first_party_caveat(f"host_uuid = {host_uuid}")
        macaroon.add_first_party_caveat(f"action = {action}")
        macaroon.add_first_party_caveat(f"nonce = {nonce}")
        return macaroon

    @patch("ticket.services.cache")
    @patch("ticket.services.AuditLog.objects")
    @patch("ticket.services.TicketRecord.objects")
    def test_verify_valid_ticket(self, mock_objects, mock_audit_objects, mock_cache):
        ticket_id = "ticket_test123"
        nonce = "test-nonce-abc"
        expires_at = timezone.now() + timedelta(minutes=5)

        macaroon = self._create_macaroon(ticket_id, self.host_uuid, "execute_command", nonce, expires_at)
        ticket_str = macaroon.serialize()

        mock_record = MagicMock()
        mock_record.ticket_id = ticket_id
        mock_record.host_uuid = uuid.UUID(self.host_uuid)
        mock_record.action = "execute_command"
        mock_record.command = None
        mock_record.nonce = nonce
        mock_record.status = 0
        mock_record.expires_at = expires_at
        mock_objects.select_for_update.return_value.get.return_value = mock_record
        mock_objects.filter.return_value.update.return_value = 1
        mock_audit_objects.create.return_value = MagicMock()
        mock_cache.get.return_value = None
        mock_cache.set.return_value = None

        result = self.service.verify_ticket(ticket=ticket_str, client_ip="127.0.0.1")
        assert result["valid"] is True
        assert result["host_uuid"] == self.host_uuid
        assert result["action"] == "execute_command"

    @patch("ticket.services.cache")
    @patch("ticket.services.AuditLog.objects")
    @patch("ticket.services.TicketRecord.objects")
    def test_verify_marks_ticket_as_used(self, mock_objects, mock_audit_objects, mock_cache):
        ticket_id = "ticket_test123"
        nonce = "test-nonce-abc"
        expires_at = timezone.now() + timedelta(minutes=5)

        macaroon = self._create_macaroon(ticket_id, self.host_uuid, "execute_command", nonce, expires_at)
        ticket_str = macaroon.serialize()

        mock_record = MagicMock()
        mock_record.ticket_id = ticket_id
        mock_record.host_uuid = uuid.UUID(self.host_uuid)
        mock_record.action = "execute_command"
        mock_record.command = None
        mock_record.nonce = nonce
        mock_record.status = 0
        mock_record.expires_at = expires_at
        mock_objects.select_for_update.return_value.get.return_value = mock_record
        mock_objects.filter.return_value.update.return_value = 1
        mock_audit_objects.create.return_value = MagicMock()
        mock_cache.get.return_value = None
        mock_cache.set.return_value = None

        self.service.verify_ticket(ticket=ticket_str, client_ip="127.0.0.1")
        mock_objects.filter.assert_called_once_with(ticket_id=ticket_id, status=0)
        mock_objects.filter.return_value.update.assert_called_once()
        update_kwargs = mock_objects.filter.return_value.update.call_args[1]
        assert update_kwargs["status"] == 1
        assert update_kwargs["used_by"] == "127.0.0.1"

    @patch("ticket.services.cache")
    @patch("ticket.services.AuditLog.objects")
    @patch("ticket.services.TicketRecord.objects")
    def test_verify_used_ticket_fails(self, mock_objects, mock_audit_objects, mock_cache):
        ticket_id = "ticket_test123"
        nonce = "test-nonce-abc"
        expires_at = timezone.now() + timedelta(minutes=5)

        macaroon = self._create_macaroon(ticket_id, self.host_uuid, "execute_command", nonce, expires_at)
        ticket_str = macaroon.serialize()

        mock_record = MagicMock()
        mock_record.status = 1
        mock_record.expires_at = expires_at
        mock_objects.select_for_update.return_value.get.return_value = mock_record

        result = self.service.verify_ticket(ticket=ticket_str)
        assert result["valid"] is False
        assert result["reason"] == "Ticket has already been used"

    def test_verify_invalid_format_fails(self):
        result = self.service.verify_ticket(ticket="invalid-ticket-string")
        assert result["valid"] is False
        assert "Invalid ticket format" in result["reason"]

    @patch("ticket.services.TicketRecord.objects")
    def test_verify_nonexistent_ticket_fails(self, mock_objects):
        m = pymacaroons.Macaroon(
            location="taurus-auth",
            identifier="ticket_nonexistent".encode(),
            key=self.service.root_key,
        )
        mock_objects.select_for_update.return_value.get.side_effect = TicketRecord.DoesNotExist

        result = self.service.verify_ticket(ticket=m.serialize())
        assert result["valid"] is False
        assert "Ticket does not exist" in result["reason"]

    @patch("ticket.services.cache")
    @patch("ticket.services.AuditLog.objects")
    @patch("ticket.services.TicketRecord.objects")
    def test_verify_creates_audit_log(self, mock_objects, mock_audit_objects, mock_cache):
        ticket_id = "ticket_test123"
        nonce = "test-nonce-abc"
        expires_at = timezone.now() + timedelta(minutes=5)

        macaroon = self._create_macaroon(ticket_id, self.host_uuid, "execute_command", nonce, expires_at)
        ticket_str = macaroon.serialize()

        mock_record = MagicMock()
        mock_record.ticket_id = ticket_id
        mock_record.host_uuid = uuid.UUID(self.host_uuid)
        mock_record.action = "execute_command"
        mock_record.command = None
        mock_record.nonce = nonce
        mock_record.status = 0
        mock_record.expires_at = expires_at
        mock_objects.select_for_update.return_value.get.return_value = mock_record
        mock_objects.filter.return_value.update.return_value = 1
        mock_audit_objects.create.return_value = MagicMock()
        mock_cache.get.return_value = None
        mock_cache.set.return_value = None

        self.service.verify_ticket(ticket=ticket_str, client_ip="10.0.0.1")
        mock_audit_objects.create.assert_called_once()
        call_kwargs = mock_audit_objects.create.call_args[1]
        assert call_kwargs["event"] == "verified"
        assert call_kwargs["result"] == "success"
        assert call_kwargs["client_ip"] == "10.0.0.1"


class TicketServiceExpiredTest(TestCase):
    def setUp(self):
        self.service = TicketService()
        self.host_uuid = str(uuid.uuid4())

    @patch("ticket.services.cache")
    @patch("ticket.services.TicketRecord.objects")
    def test_verify_expired_ticket_fails(self, mock_objects, mock_cache):
        ticket_id = "ticket_expired123"
        nonce = "expired-nonce"
        expires_at = timezone.now() - timedelta(minutes=1)

        macaroon = pymacaroons.Macaroon(
            location="taurus-auth",
            identifier=ticket_id.encode(),
            key=self.service.root_key,
        )
        macaroon.add_first_party_caveat(f"time < {expires_at.isoformat()}")
        macaroon.add_first_party_caveat(f"host_uuid = {self.host_uuid}")
        macaroon.add_first_party_caveat(f"action = execute_command")
        macaroon.add_first_party_caveat(f"nonce = {nonce}")

        mock_record = MagicMock()
        mock_record.status = 0
        mock_record.expires_at = expires_at
        mock_record.nonce = nonce
        mock_objects.select_for_update.return_value.get.return_value = mock_record
        mock_objects.filter.return_value.update.return_value = 1

        result = self.service.verify_ticket(ticket=macaroon.serialize())
        assert result["valid"] is False
        assert "Ticket has expired" in result["reason"]

    @patch("ticket.services.cache")
    @patch("ticket.services.TicketRecord.objects")
    def test_expired_ticket_status_updated(self, mock_objects, mock_cache):
        ticket_id = "ticket_expired456"
        nonce = "expired-nonce2"
        expires_at = timezone.now() - timedelta(minutes=1)

        macaroon = pymacaroons.Macaroon(
            location="taurus-auth",
            identifier=ticket_id.encode(),
            key=self.service.root_key,
        )
        macaroon.add_first_party_caveat(f"time < {expires_at.isoformat()}")
        macaroon.add_first_party_caveat(f"host_uuid = {self.host_uuid}")
        macaroon.add_first_party_caveat(f"action = execute_command")
        macaroon.add_first_party_caveat(f"nonce = {nonce}")

        mock_record = MagicMock()
        mock_record.status = 0
        mock_record.expires_at = expires_at
        mock_record.nonce = nonce
        mock_objects.select_for_update.return_value.get.return_value = mock_record
        mock_objects.filter.return_value.update.return_value = 1

        self.service.verify_ticket(ticket=macaroon.serialize())
        mock_objects.filter.assert_called()


class TicketServiceRevokeTest(TestCase):
    def setUp(self):
        self.service = TicketService()
        self.host_uuid = str(uuid.uuid4())

    @patch("ticket.services.cache")
    @patch("ticket.services.AuditLog.objects")
    @patch("ticket.services.TicketRecord.objects")
    def test_revoke_valid_ticket(self, mock_objects, mock_audit_objects, mock_cache):
        mock_record = MagicMock()
        mock_record.status = 0
        mock_objects.get.return_value = mock_record
        mock_audit_objects.create.return_value = MagicMock()

        self.service.revoke_ticket("ticket_test123")
        assert mock_record.status == 3
        mock_record.save.assert_called_once()

    @patch("ticket.services.cache")
    @patch("ticket.services.AuditLog.objects")
    @patch("ticket.services.TicketRecord.objects")
    def test_revoke_creates_audit_log(self, mock_objects, mock_audit_objects, mock_cache):
        mock_record = MagicMock()
        mock_record.status = 0
        mock_objects.get.return_value = mock_record
        mock_audit_objects.create.return_value = MagicMock()

        self.service.revoke_ticket("ticket_test123", reason="security")
        mock_audit_objects.create.assert_called_once()
        call_kwargs = mock_audit_objects.create.call_args[1]
        assert call_kwargs["event"] == "revoked"
        assert call_kwargs["result"] == "success"
        assert call_kwargs["detail"]["reason"] == "security"

    @patch("ticket.services.TicketRecord.objects")
    def test_revoke_nonexistent_ticket_raises(self, mock_objects):
        mock_objects.get.side_effect = TicketRecord.DoesNotExist

        with pytest.raises(ValueError, match="Ticket does not exist"):
            self.service.revoke_ticket("nonexistent_id")

    @patch("ticket.services.TicketRecord.objects")
    def test_revoke_used_ticket_raises(self, mock_objects):
        mock_record = MagicMock()
        mock_record.status = 1
        mock_record.get_status_display.return_value = "Used"
        mock_objects.get.return_value = mock_record

        with pytest.raises(ValueError, match="cannot be revoked"):
            self.service.revoke_ticket("ticket_test123")

    @patch("ticket.services.cache")
    @patch("ticket.services.AuditLog.objects")
    @patch("ticket.services.TicketRecord.objects")
    def test_verify_revoked_ticket_fails(self, mock_objects, mock_audit_objects, mock_cache):
        ticket_id = "ticket_revoked123"
        nonce = "revoked-nonce"
        expires_at = timezone.now() + timedelta(minutes=5)

        macaroon = pymacaroons.Macaroon(
            location="taurus-auth",
            identifier=ticket_id.encode(),
            key=self.service.root_key,
        )
        macaroon.add_first_party_caveat(f"time < {expires_at.isoformat()}")
        macaroon.add_first_party_caveat(f"host_uuid = {self.host_uuid}")
        macaroon.add_first_party_caveat(f"action = execute_command")
        macaroon.add_first_party_caveat(f"nonce = {nonce}")

        mock_record = MagicMock()
        mock_record.status = 3
        mock_record.expires_at = expires_at
        mock_objects.select_for_update.return_value.get.return_value = mock_record

        result = self.service.verify_ticket(ticket=macaroon.serialize())
        assert result["valid"] is False
        assert "Ticket has been revoked" in result["reason"]