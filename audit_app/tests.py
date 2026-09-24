from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from audit_app.models import ActivityLog
from audit_app.context import extract_client_ip, parse_device_info, set_audit_context
from audit_app.middleware import AuditContextMiddleware
from audit_app.services import compute_model_diff, log_audit_event

User = get_user_model()


class AuditContextAndUtilitiesTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_extract_client_ip_from_remote_addr(self):
        request = self.factory.get('/audit/', REMOTE_ADDR='192.168.1.50')
        ip = extract_client_ip(request)
        self.assertEqual(ip, '192.168.1.50')

    def test_extract_client_ip_from_x_forwarded_for(self):
        request = self.factory.get(
            '/audit/',
            HTTP_X_FORWARDED_FOR='203.0.113.195, 198.51.100.17',
            REMOTE_ADDR='10.0.0.1'
        )
        ip = extract_client_ip(request)
        self.assertEqual(ip, '203.0.113.195')

    def test_extract_client_ip_from_x_real_ip(self):
        request = self.factory.get(
            '/audit/',
            HTTP_X_REAL_IP='198.51.100.42',
            REMOTE_ADDR='10.0.0.1'
        )
        ip = extract_client_ip(request)
        self.assertEqual(ip, '198.51.100.42')

    def test_parse_device_info_desktop_chrome(self):
        ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
        info = parse_device_info(ua)
        self.assertEqual(info['device_type'], 'Desktop')
        self.assertIn('Windows', info['os'])
        self.assertEqual(info['browser'], 'Chrome 128')

    def test_parse_device_info_mobile_iphone(self):
        ua = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1"
        info = parse_device_info(ua)
        self.assertEqual(info['device_type'], 'Mobile')
        self.assertEqual(info['os'], 'iOS 17.5')
        self.assertEqual(info['browser'], 'Safari 17')

    def test_parse_device_info_tablet_ipad(self):
        ua = "Mozilla/5.0 (iPad; CPU OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1"
        info = parse_device_info(ua)
        self.assertEqual(info['device_type'], 'Tablet')
        self.assertEqual(info['os'], 'iOS 16.6')

    def test_parse_device_info_bot(self):
        ua = "Googlebot/2.1 (+http://www.google.com/bot.html)"
        info = parse_device_info(ua)
        self.assertEqual(info['device_type'], 'Bot')


class AuditModelAndServiceTestCase(TestCase):
    def setUp(self):
        self.advisor_group = Group.objects.create(name='Service Advisor')
        self.user = User.objects.create_user(
            username='service_advisor_1',
            password='testpassword123',
            is_staff=True
        )
        self.user.groups.add(self.advisor_group)

    def test_log_audit_event_direct(self):
        set_audit_context({
            'ip_address': '10.20.30.40',
            'correlation_id': 'test-trace-123',
            'device_type': 'Desktop',
            'browser': 'Chrome 128',
            'os': 'Windows 10/11',
            'user_agent': 'Test Agent',
            'user': self.user
        })

        diff = {'status': {'old': 'Open', 'new': 'In Progress'}}
        desc = "Updated status of Job Card #JC-2026-001 from 'Open' to 'In Progress'"

        entry = log_audit_event(
            action='STATUS_CHANGE',
            module='JOBCARD',
            entity_type='JobCard',
            entity_id='101',
            entity_reference='JC-2026-001',
            description=desc,
            changes_diff=diff,
            user=self.user
        )

        self.assertIsNotNone(entry)
        self.assertEqual(entry.action_type, 'STATUS_CHANGE')
        self.assertEqual(entry.module, 'JOBCARD')
        self.assertEqual(entry.entity_type, 'JobCard')
        self.assertEqual(entry.entity_id, '101')
        self.assertEqual(entry.entity_reference, 'JC-2026-001')
        self.assertEqual(entry.user_username, 'service_advisor_1')
        self.assertEqual(entry.user_role, 'Service Advisor')
        self.assertEqual(entry.ip_address, '10.20.30.40')
        self.assertEqual(entry.device_type, 'Desktop')
        self.assertEqual(entry.browser, 'Chrome 128')
        self.assertEqual(entry.operating_system, 'Windows 10/11')
        self.assertEqual(entry.changes_diff, diff)
        self.assertIn('JC-2026-001', entry.description)
        self.assertIsNotNone(entry.created_at)

    def test_compute_model_diff(self):
        class DummyInstance:
            status = 'draft'
            amount_paid = 100
            payment_mode = 'cash'
            _meta = None

        old = DummyInstance()
        new_data = {
            'status': 'paid',
            'amount_paid': 500,
            'payment_mode': 'cash'
        }

        diff, descs = compute_model_diff(old, new_data, monitored_fields=['status', 'amount_paid', 'payment_mode'])
        self.assertIn('status', diff)
        self.assertEqual(diff['status']['old'], 'draft')
        self.assertEqual(diff['status']['new'], 'paid')
        self.assertIn('amount_paid', diff)
        self.assertNotIn('payment_mode', diff)  # Unchanged
        self.assertEqual(len(descs), 2)


class AuditMiddlewareTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = AuditContextMiddleware(get_response=lambda req: None)

    def test_middleware_captures_context(self):
        request = self.factory.get(
            '/audit/',
            HTTP_USER_AGENT="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/128.0.0.0",
            HTTP_X_FORWARDED_FOR='172.16.0.25'
        )

        self.middleware.process_request(request)

        self.assertTrue(hasattr(request, 'correlation_id'))
        from audit_app.context import get_audit_context
        ctx = get_audit_context()
        self.assertEqual(ctx.get('ip_address'), '172.16.0.25')
        self.assertEqual(ctx.get('device_type'), 'Desktop')
        self.assertEqual(ctx.get('browser'), 'Chrome 128')

