import uuid
from django.utils.deprecation import MiddlewareMixin
from audit_app.context import set_audit_context, extract_client_ip, parse_device_info


class AuditContextMiddleware(MiddlewareMixin):
    """
    Captures incoming request metadata (IP address, Device info, Browser, Correlation ID)
    into a thread-safe context variable for seamless audit logging.
    """
    def process_request(self, request):
        ip_addr = extract_client_ip(request)
        ua_raw = request.META.get('HTTP_USER_AGENT', '')
        device_info = parse_device_info(ua_raw)
        
        correlation_id = request.headers.get('X-Correlation-ID') or str(uuid.uuid4())
        request.correlation_id = correlation_id

        context = {
            'ip_address': ip_addr,
            'correlation_id': correlation_id,
            'device_type': device_info['device_type'],
            'browser': device_info['browser'],
            'os': device_info['os'],
            'user_agent': device_info['user_agent'],
            'user': getattr(request, 'user', None) if getattr(request, 'user', None) and request.user.is_authenticated else None,
        }
        request._audit_token = set_audit_context(context)

    def process_response(self, request, response):
        if hasattr(request, 'correlation_id'):
            response['X-Correlation-ID'] = request.correlation_id
        return response
