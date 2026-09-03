"""
Ticket Service - Core business logic
"""
import secrets
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from django.conf import settings
from django.core.cache import cache
from django.db import transaction
from django.utils import timezone

import pymacaroons

from .models import TicketRecord, AuditLog

logger = logging.getLogger('ticket')


class TicketService:
    """Ticket service"""
    
    def __init__(self):
        self.root_key = settings.MACAROON_ROOT_KEY.encode()
    
    def generate_ticket(self, host_uuid: str, action: str = 'execute_command',
                       command: Optional[str] = None, expires_minutes: int = None,
                       metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Generate a ticket
        
        Args:
            host_uuid: Host UUID
            action: Allowed action
            command: Allowed command to execute (optional)
            expires_minutes: Expiration time in minutes
            metadata: Metadata
            
        Returns:
            Dictionary containing ticket information
        """
        if expires_minutes is None:
            expires_minutes = settings.TICKET_DEFAULT_EXPIRES_MINUTES
        
        expires_minutes = min(expires_minutes, settings.TICKET_MAX_EXPIRES_MINUTES)
        
        ticket_id = f"ticket_{secrets.token_urlsafe(16)}"
        nonce = secrets.token_urlsafe(32)
        expires_at = timezone.now() + timedelta(minutes=expires_minutes)
        
        macaroon = pymacaroons.Macaroon(
            location='taurus-auth',
            identifier=ticket_id.encode(),
            key=self.root_key
        )
        
        macaroon.add_first_party_caveat(f'time < {expires_at.isoformat()}')
        macaroon.add_first_party_caveat(f'host_uuid = {host_uuid}')
        macaroon.add_first_party_caveat(f'action = {action}')
        
        if command:
            macaroon.add_first_party_caveat(f'command = {command}')
        
        macaroon.add_first_party_caveat(f'nonce = {nonce}')
        
        ticket_serialized = macaroon.serialize()
        
        with transaction.atomic():
            ticket_record = TicketRecord.objects.create(
                ticket_id=ticket_id,
                host_uuid=host_uuid,
                action=action,
                command=command,
                nonce=nonce,
                expires_at=expires_at,
                metadata=metadata or {},
            )
            
            AuditLog.objects.create(
                ticket_id=ticket_id,
                event='generated',
                host_uuid=host_uuid,
                result='success',
                detail={
                    'action': action,
                    'command': command,
                    'expires_at': expires_at.isoformat(),
                }
            )
        
        logger.info(f"Ticket generated successfully: ticket_id={ticket_id}, host={host_uuid}")
        
        return {
            'ticket': ticket_serialized,
            'ticket_id': ticket_id,
            'nonce': nonce,
            'expires_at': expires_at,
            'host_uuid': host_uuid,
            'action': action,
            'command': command,
        }
    
    def verify_ticket(self, ticket: str, client_ip: Optional[str] = None) -> Dict[str, Any]:
        """
        Verify a ticket
        
        Args:
            ticket: Ticket string
            client_ip: Client IP
            
        Returns:
            Verification result
        """
        try:
            macaroon = pymacaroons.Macaroon.deserialize(ticket)
        except Exception as e:
            logger.warning(f"Ticket deserialization failed: {e}")
            return {'valid': False, 'reason': 'Invalid ticket format'}
        
        ticket_id = macaroon.identifier.decode() if isinstance(macaroon.identifier, bytes) else macaroon.identifier
        
        try:
            with transaction.atomic():
                ticket_record = TicketRecord.objects.select_for_update().get(ticket_id=ticket_id)
        except TicketRecord.DoesNotExist:
            return {'valid': False, 'reason': 'Ticket does not exist'}
        
        if ticket_record.status == 1:
            return {'valid': False, 'reason': 'Ticket has already been used'}
        if ticket_record.status == 2:
            return {'valid': False, 'reason': 'Ticket has expired'}
        if ticket_record.status == 3:
            return {'valid': False, 'reason': 'Ticket has been revoked'}
        
        if ticket_record.expires_at < timezone.now():
            TicketRecord.objects.filter(ticket_id=ticket_id).update(status=2)
            return {'valid': False, 'reason': 'Ticket has expired'}
        
        nonce_key = f"ticket_nonce:{ticket_record.nonce}"
        if cache.get(nonce_key):
            return {'valid': False, 'reason': 'Ticket has already been used'}
        
        verifier = pymacaroons.Verifier()
        
        def verify_time(caveat: str) -> bool:
            if caveat.startswith('time < '):
                time_str = caveat.replace('time < ', '')
                expiry = datetime.fromisoformat(time_str)
                if expiry.tzinfo is None:
                    expiry = timezone.make_aware(expiry)
                return timezone.now() < expiry
            return True
        
        def verify_host_uuid(caveat: str) -> bool:
            if caveat.startswith('host_uuid = '):
                return caveat[len('host_uuid = '):] == str(ticket_record.host_uuid)
            return True

        def verify_action(caveat: str) -> bool:
            if caveat.startswith('action = '):
                return caveat[len('action = '):] == ticket_record.action
            return True

        def verify_command(caveat: str) -> bool:
            if caveat.startswith('command = '):
                return caveat[len('command = '):] == ticket_record.command
            return True

        def verify_nonce(caveat: str) -> bool:
            if caveat.startswith('nonce = '):
                return caveat[len('nonce = '):] == ticket_record.nonce
            return True
        
        verifier.satisfy_general(verify_time)
        verifier.satisfy_general(verify_host_uuid)
        verifier.satisfy_general(verify_action)
        verifier.satisfy_general(verify_command)
        verifier.satisfy_general(verify_nonce)
        
        try:
            is_valid = verifier.verify(macaroon, self.root_key)
        except Exception as e:
            logger.warning(f"Ticket verification failed: {e}")
            return {'valid': False, 'reason': 'Ticket verification failed'}
        
        if not is_valid:
            return {'valid': False, 'reason': 'Invalid ticket signature'}
        
        with transaction.atomic():
            updated = TicketRecord.objects.filter(
                ticket_id=ticket_id,
                status=0
            ).update(
                status=1,
                used_at=timezone.now(),
                used_by=client_ip,
            )
            
            if updated == 0:
                return {'valid': False, 'reason': 'Ticket has already been used'}
            
            cache.set(nonce_key, "used", timeout=3600)
            
            AuditLog.objects.create(
                ticket_id=ticket_id,
                event='verified',
                host_uuid=ticket_record.host_uuid,
                client_ip=client_ip,
                result='success',
            )
        
        logger.info(f"Ticket verified successfully: ticket_id={ticket_id}, client_ip={client_ip}")
        
        return {
            'valid': True,
            'host_uuid': str(ticket_record.host_uuid),
            'action': ticket_record.action,
            'command': ticket_record.command,
        }
    
    def revoke_ticket(self, ticket_id: str, reason: Optional[str] = None) -> bool:
        """
        Revoke a ticket
        
        Args:
            ticket_id: Ticket ID
            reason: Revocation reason
            
        Returns:
            Whether the operation was successful
        """
        try:
            ticket_record = TicketRecord.objects.get(ticket_id=ticket_id)
        except TicketRecord.DoesNotExist:
            raise ValueError("Ticket does not exist")
        
        if ticket_record.status != 0:
            raise ValueError(f"Ticket status is {ticket_record.get_status_display()}, cannot be revoked")
        
        with transaction.atomic():
            ticket_record.status = 3
            ticket_record.save(update_fields=['status', 'updated_at'])
            
            AuditLog.objects.create(
                ticket_id=ticket_id,
                event='revoked',
                host_uuid=ticket_record.host_uuid,
                result='success',
                detail={'reason': reason},
            )
        
        logger.info(f"Ticket revoked: ticket_id={ticket_id}, reason={reason}")
        
        return True