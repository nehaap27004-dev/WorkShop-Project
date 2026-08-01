from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from item_master.models import Item, Unit
from accounts_app.models import LedgerCreation

from .models import WorkshopStaff, WorkshopVehicle, VehicleInspection, InspectionFinding, ServiceCategory, JobCard


class InspectionCreateViewTests(TestCase):
    def test_inspector_dropdown_includes_inspector_staff(self):
        staff = WorkshopStaff.objects.create(
            full_name='John Inspector',
            role='Inspector',
            phone='1234567890',
            join_date=timezone.now().date(),
            status='active',
            is_active=True,
        )

        response = self.client.get(reverse('jobcard_app:inspection_create'))

        self.assertEqual(response.status_code, 200)
        self.assertIn(staff, response.context['inspectors'])
        self.assertContains(response, 'John Inspector')


class JobCardCreateViewTests(TestCase):
    def test_jobcard_page_includes_technician_staff(self):
        user = get_user_model().objects.create_user(username='tester', password='secret123')
        self.client.force_login(user)

        staff = WorkshopStaff.objects.create(
            full_name='Ali Technician',
            role='technician',
            phone='1234567890',
            join_date=timezone.now().date(),
            status='active',
            is_active=True,
        )

        response = self.client.get(reverse('jobcard_app:jobcard_create'))

        self.assertEqual(response.status_code, 200)
        self.assertIn(staff, response.context['technicians'])
        self.assertContains(response, 'Ali Technician')

    def test_jobcard_page_includes_item_master_items(self):
        user = get_user_model().objects.create_user(username='tester', password='secret123')
        self.client.force_login(user)

        unit = Unit.objects.create(unit_code='PCS', unit_name='Pieces')
        item = Item.objects.create(
            item_name='Brake Pad',
            item_code='BP-001',
            item_unit=unit,
        )

        response = self.client.get(reverse('jobcard_app:jobcard_create'))

        self.assertEqual(response.status_code, 200)
        self.assertIn(item, response.context['items'])
        self.assertContains(response, 'Brake Pad')

    def test_jobcard_page_includes_service_categories(self):
        user = get_user_model().objects.create_user(username='tester', password='secret123')
        self.client.force_login(user)

        category = ServiceCategory.objects.create(name='Brakes', description='Brake services')

        response = self.client.get(reverse('jobcard_app:jobcard_create'))

        self.assertEqual(response.status_code, 200)
        self.assertIn(category, response.context['categories'])
        self.assertContains(response, 'name="complaint_category[]"')
        self.assertContains(response, 'Brakes')

    def test_jobcard_page_offers_inspection_load_selector(self):
        user = get_user_model().objects.create_user(username='tester', password='secret123')
        self.client.force_login(user)

        customer = LedgerCreation.objects.create(ledger_name='Test Customer')
        vehicle = WorkshopVehicle.objects.create(
            customer=customer,
            registration_number='ABC-1234',
            make='Toyota',
            model='Corolla',
        )
        inspection = VehicleInspection.objects.create(
            customer=customer,
            vehicle=vehicle,
            inspection_date=timezone.now().date(),
            fuel_level='1/2',
        )

        response = self.client.get(reverse('jobcard_app:jobcard_create'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="from_inspection"')
        self.assertContains(response, str(inspection.pk))

    def test_jobcard_page_prefills_inspection_findings(self):
        user = get_user_model().objects.create_user(username='tester', password='secret123')
        self.client.force_login(user)

        customer = LedgerCreation.objects.create(ledger_name='Test Customer')
        vehicle = WorkshopVehicle.objects.create(
            customer=customer,
            registration_number='ABC-9999',
            make='Toyota',
            model='Yaris',
        )
        inspection = VehicleInspection.objects.create(
            customer=customer,
            vehicle=vehicle,
            inspection_date=timezone.now().date(),
            fuel_level='1/2',
        )
        InspectionFinding.objects.create(
            inspection=inspection,
            finding_type='finding',
            description='Brake fluid low',
            order=1,
        )

        response = self.client.get(reverse('jobcard_app:jobcard_create') + f'?from_inspection={inspection.pk}')

        self.assertEqual(response.status_code, 200)
        self.assertIn('Brake fluid low', response.context['prefill_findings'])
        self.assertContains(response, 'Brake fluid low')

    def test_jobcard_page_prefills_from_inspection_complaints_and_categories(self):
        user = get_user_model().objects.create_user(username='tester', password='secret123')
        self.client.force_login(user)

        customer = LedgerCreation.objects.create(ledger_name='Test Customer')
        vehicle = WorkshopVehicle.objects.create(
            customer=customer,
            registration_number='ABC-1234',
            make='Toyota',
            model='Corolla',
        )
        inspection = VehicleInspection.objects.create(
            customer=customer,
            vehicle=vehicle,
            inspection_date=timezone.now().date(),
            fuel_level='1/2',
        )
        ServiceCategory.objects.create(name='AC', description='Air conditioning')
        InspectionFinding.objects.create(
            inspection=inspection,
            finding_type='complaint',
            description='AC not cooling',
            order=1,
        )

        response = self.client.get(reverse('jobcard_app:jobcard_create') + f'?from_inspection={inspection.pk}')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['prefill_inspection'], inspection)
        self.assertContains(response, 'AC not cooling')
        self.assertContains(response, 'AC')

    def test_jobcard_create_saves_findings_from_form(self):
        user = get_user_model().objects.create_user(username='tester', password='secret123')
        self.client.force_login(user)

        customer = LedgerCreation.objects.create(ledger_name='Test Customer')
        vehicle = WorkshopVehicle.objects.create(
            customer=customer,
            registration_number='ABC-7777',
            make='Toyota',
            model='Camry',
        )

        response = self.client.post(reverse('jobcard_app:jobcard_create'), {
            'customer': customer.pk,
            'date': timezone.now().date().strftime('%Y-%m-%d'),
            'vehicle': vehicle.pk,
            'priority': 'normal',
            'status': 'open',
            'complaint_category[]': [''],
            'complaint_description[]': [''],
            'complaint_type[]': ['Mechanical'],
            'complaint_technician[]': [''],
            'complaint_status[]': ['Open'],
            'finding_description[]': ['Brake fluid low'],
            'finding_technician[]': [''],
            'finding_status[]': ['Pending'],
        })

        self.assertEqual(response.status_code, 302)
        job_card = JobCard.objects.order_by('-created_on').first()
        self.assertIsNotNone(job_card)
        self.assertTrue(job_card.findings.filter(description='Brake fluid low').exists())

    def test_jobcard_create_saves_complaint_from_inspection_and_links_inspection(self):
        user = get_user_model().objects.create_user(username='tester', password='secret123')
        self.client.force_login(user)

        customer = LedgerCreation.objects.create(ledger_name='Test Customer')
        vehicle = WorkshopVehicle.objects.create(
            customer=customer,
            registration_number='ABC-1235',
            make='Honda',
            model='Civic',
        )
        inspection = VehicleInspection.objects.create(
            customer=customer,
            vehicle=vehicle,
            inspection_date=timezone.now().date(),
            fuel_level='1/2',
        )
        ServiceCategory.objects.create(name='AC', description='Air conditioning')
        InspectionFinding.objects.create(
            inspection=inspection,
            finding_type='complaint',
            description='AC not cooling',
            order=1,
        )

        response = self.client.post(reverse('jobcard_app:jobcard_create'), {
            'customer': customer.pk,
            'date': timezone.now().date().strftime('%Y-%m-%d'),
            'vehicle': vehicle.pk,
            'priority': 'normal',
            'status': 'open',
            'complaint_category[]': ['AC'],
            'complaint_description[]': ['AC not cooling'],
            'complaint_type[]': ['AC'],
            'complaint_technician[]': [''],
            'complaint_status[]': ['Open'],
            'source_inspection_id': str(inspection.pk),
        })

        self.assertEqual(response.status_code, 302)
        job_card = JobCard.objects.order_by('-created_on').first()
        self.assertIsNotNone(job_card)
        self.assertTrue(job_card.complaints.filter(description='AC not cooling').exists())
        self.assertEqual(job_card.complaints.get().category, 'AC')
        inspection.refresh_from_db()
        self.assertEqual(inspection.job_card, job_card)
