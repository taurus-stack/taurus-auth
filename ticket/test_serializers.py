"""
ticket/serializers.py serializer unit tests

Test contents:
1. GenerateTicketRequestSerializer - Validate request parameters
2. VerifyTicketRequestSerializer - Validate request parameters
3. RevokeTicketRequestSerializer - Validate request parameters
"""
import uuid

from django.test import TestCase

from ticket.serializers import (
    GenerateTicketRequestSerializer,
    VerifyTicketRequestSerializer,
    RevokeTicketRequestSerializer,
)


class GenerateTicketRequestSerializerTest(TestCase):
    def test_valid_data(self):
        data = {
            "host_uuid": str(uuid.uuid4()),
            "action": "execute_command",
        }
        serializer = GenerateTicketRequestSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

    def test_missing_host_uuid(self):
        data = {"action": "execute_command"}
        serializer = GenerateTicketRequestSerializer(data=data)
        assert not serializer.is_valid()
        assert "host_uuid" in serializer.errors

    def test_invalid_host_uuid(self):
        data = {"host_uuid": "not-a-uuid", "action": "execute_command"}
        serializer = GenerateTicketRequestSerializer(data=data)
        assert not serializer.is_valid()
        assert "host_uuid" in serializer.errors

    def test_default_action(self):
        data = {"host_uuid": str(uuid.uuid4())}
        serializer = GenerateTicketRequestSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["action"] == "execute_command"

    def test_default_expires_minutes(self):
        data = {"host_uuid": str(uuid.uuid4())}
        serializer = GenerateTicketRequestSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["expires_minutes"] == 5

    def test_expires_minutes_min_value(self):
        data = {"host_uuid": str(uuid.uuid4()), "expires_minutes": 0}
        serializer = GenerateTicketRequestSerializer(data=data)
        assert not serializer.is_valid()

    def test_expires_minutes_max_value(self):
        data = {"host_uuid": str(uuid.uuid4()), "expires_minutes": 61}
        serializer = GenerateTicketRequestSerializer(data=data)
        assert not serializer.is_valid()

    def test_with_command(self):
        data = {
            "host_uuid": str(uuid.uuid4()),
            "action": "execute_command",
            "command": "ls -la",
        }
        serializer = GenerateTicketRequestSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["command"] == "ls -la"

    def test_with_metadata(self):
        data = {
            "host_uuid": str(uuid.uuid4()),
            "action": "execute_command",
            "metadata": {"source": "test"},
        }
        serializer = GenerateTicketRequestSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["metadata"] == {"source": "test"}


class VerifyTicketRequestSerializerTest(TestCase):
    def test_valid_data(self):
        data = {"ticket": "some-ticket-string"}
        serializer = VerifyTicketRequestSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

    def test_missing_ticket(self):
        data = {}
        serializer = VerifyTicketRequestSerializer(data=data)
        assert not serializer.is_valid()
        assert "ticket" in serializer.errors

    def test_with_client_ip(self):
        data = {"ticket": "some-ticket", "client_ip": "10.0.0.1"}
        serializer = VerifyTicketRequestSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["client_ip"] == "10.0.0.1"


class RevokeTicketRequestSerializerTest(TestCase):
    def test_valid_with_reason(self):
        data = {"reason": "security incident"}
        serializer = RevokeTicketRequestSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["reason"] == "security incident"

    def test_valid_without_reason(self):
        data = {}
        serializer = RevokeTicketRequestSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data.get("reason") is None