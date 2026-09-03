"""
Ticket views / API endpoints
"""
import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.conf import settings
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

from .models import TicketRecord, AuditLog
from .serializers import (
    GenerateTicketRequestSerializer,
    GenerateTicketResponseSerializer,
    VerifyTicketRequestSerializer,
    VerifyTicketResponseSerializer,
    RevokeTicketRequestSerializer,
    TicketRecordSerializer,
    AuditLogSerializer,
)
from .services import TicketService

logger = logging.getLogger('ticket')

jwt_authenticator = JWTAuthentication()


def verify_backend_auth(request):
    """Verify backend service JWT authentication"""
    try:
        auth_result = jwt_authenticator.authenticate(request)
        if auth_result is None:
            return False
        
        user, token = auth_result
        
        allowed_services = getattr(settings, 'ALLOWED_BACKEND_SERVICES', ['taurus-backend'])
        # SIMPLE_JWT USER_ID_CLAIM is configured as user_id, also supports sub
        service_id = token.get('user_id', '') or token.get('sub', '')
        
        if service_id not in allowed_services:
            logger.warning(f"Unauthorized service: {service_id}")
            return False
        
        return True
    except (InvalidToken, TokenError) as e:
        logger.warning(f"JWT verification failed: {e}")
        return False
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        return False


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """Health check"""
    return Response({
        'code': 2000,
        'msg': 'ok',
        'data': {
            'service': 'taurus-auth',
            'status': 'healthy',
        }
    })


@method_decorator(csrf_exempt, name='dispatch')
class TicketViewSet(viewsets.ViewSet):
    """Ticket ViewSet"""
    
    permission_classes = [AllowAny]
    
    @action(detail=False, methods=['post'], url_path='generate')
    def generate(self, request):
        """
        Generate a ticket (callable only by backend, requires JWT auth)
        """
        if not verify_backend_auth(request):
            return Response(
                {'code': 4001, 'msg': 'Authentication failed: invalid JWT Token'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        serializer = GenerateTicketRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            service = TicketService()
            result = service.generate_ticket(
                host_uuid=str(serializer.validated_data['host_uuid']),
                action=serializer.validated_data['action'],
                command=serializer.validated_data.get('command'),
                expires_minutes=serializer.validated_data.get('expires_minutes'),
                metadata=serializer.validated_data.get('metadata', {}),
            )
            
            response_serializer = GenerateTicketResponseSerializer(data=result)
            response_serializer.is_valid(raise_exception=True)
            
            return Response({
                'code': 2000,
                'msg': 'Ticket generated successfully',
                'data': response_serializer.data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Ticket generation failed: {e}")
            return Response(
                {'code': 5000, 'msg': f'Ticket generation failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'], url_path='verify')
    def verify(self, request):
        """
        Verify a ticket (called by executor)
        """
        serializer = VerifyTicketRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            service = TicketService()
            result = service.verify_ticket(
                ticket=serializer.validated_data['ticket'],
                client_ip=serializer.validated_data.get('client_ip'),
            )
            
            response_serializer = VerifyTicketResponseSerializer(data=result)
            response_serializer.is_valid(raise_exception=True)
            
            return Response({
                'code': 2000 if result['valid'] else 4000,
                'msg': 'Verification successful' if result['valid'] else result.get('reason', 'Verification failed'),
                'data': response_serializer.data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Ticket verification failed: {e}")
            return Response(
                {'code': 5000, 'msg': f'Ticket verification failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'], url_path='revoke')
    def revoke(self, request, pk=None):
        """
        Revoke a ticket (callable only by backend)
        """
        if not verify_backend_auth(request):
            return Response(
                {'code': 4001, 'msg': 'Invalid authentication token'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        serializer = RevokeTicketRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            service = TicketService()
            service.revoke_ticket(
                ticket_id=pk,
                reason=serializer.validated_data.get('reason'),
            )
            
            return Response({
                'code': 2000,
                'msg': 'Ticket revoked'
            }, status=status.HTTP_200_OK)
            
        except ValueError as e:
            return Response(
                {'code': 4000, 'msg': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Ticket revocation failed: {e}")
            return Response(
                {'code': 5000, 'msg': f'Ticket revocation failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'], url_path='list')
    def list_tickets(self, request):
        """
        Query ticket list (callable only by backend)
        """
        if not verify_backend_auth(request):
            return Response(
                {'code': 4001, 'msg': 'Invalid authentication token'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        host_uuid = request.query_params.get('host_uuid')
        status_filter = request.query_params.get('status')
        
        queryset = TicketRecord.objects.all()
        
        if host_uuid:
            queryset = queryset.filter(host_uuid=host_uuid)
        if status_filter is not None:
            queryset = queryset.filter(status=int(status_filter))
        
        queryset = queryset.order_by('-created_at')
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = TicketRecordSerializer(page, many=True)
            return self.get_paginated_response({
                'code': 2000,
                'data': serializer.data
            })
        
        serializer = TicketRecordSerializer(queryset, many=True)
        return Response({
            'code': 2000,
            'data': serializer.data
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'], url_path='audit-logs')
    def audit_logs(self, request):
        """
        Query audit logs (callable only by backend)
        """
        if not verify_backend_auth(request):
            return Response(
                {'code': 4001, 'msg': 'Invalid authentication token'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        ticket_id = request.query_params.get('ticket_id')
        event = request.query_params.get('event')
        
        queryset = AuditLog.objects.all()
        
        if ticket_id:
            queryset = queryset.filter(ticket_id=ticket_id)
        if event:
            queryset = queryset.filter(event=event)
        
        queryset = queryset.order_by('-created_at')
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = AuditLogSerializer(page, many=True)
            return self.get_paginated_response({
                'code': 2000,
                'data': serializer.data
            })
        
        serializer = AuditLogSerializer(queryset, many=True)
        return Response({
            'code': 2000,
            'data': serializer.data
        }, status=status.HTTP_200_OK)