from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from item_master.models import Item, Unit
from accounts_app.models import LedgerCreation

from fleet_app.models import Staff, StaffCategory, Manufacturer, VehicleModel, VehicleCategory
from .models import WorkshopVehicle, VehicleInspection, InspectionFinding, ServiceCategory, JobCard


def create_test_vehicle(customer, registration_number, make_name='Toyota', model_name='Corolla'):
    cat, _ = VehicleCategory.objects.get_or_create(category_name='Sedan')
    mfr, _ = Manufacturer.objects.get_or_create(manufacturer_name=make_name)
    vmodel, _ = VehicleModel.objects.get_or_create(
        manufacturer=mfr,
        model_name=model_name,
        defaults={'vehicle_category': cat}
    )
    return WorkshopVehicle.objects.create(
        customer=customer,
        registration_number=registration_number,
        manufacturer=mfr,
        vehicle_model=vmodel,
    )


class InspectionCreateViewTests(TestCase):
    def test_inspector_dropdown_includes_inspector_staff(self):
        cat, _ = StaffCategory.objects.get_or_create(name='Inspector')
        staff = Staff.objects.create(
            staff_id='INS-001',
            full_name='John Inspector',
            staff_category=cat,
            contact_number='1234567890',
            status='Active',
        )

        response = self.client.get(reverse('jobcard_app:inspection_create'))

        self.assertEqual(response.status_code, 200)
        self.assertIn(staff, response.context['inspectors'])
        self.assertContains(response, 'John Inspector')


class JobCardCreateViewTests(TestCase):
    def test_jobcard_page_includes_technician_staff(self):
        user = get_user_model().objects.create_user(username='tester', password='secret123')
        self.client.force_login(user)

        cat, _ = StaffCategory.objects.get_or_create(name='Technician')
        staff = Staff.objects.create(
            staff_id='TECH-001',
            full_name='Ali Technician',
            staff_category=cat,
            contact_number='1234567890',
            status='Active',
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
        vehicle = create_test_vehicle(customer, 'ABC-1234', 'Toyota', 'Corolla')
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
        vehicle = create_test_vehicle(customer, 'ABC-9999', 'Toyota', 'Yaris')
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
        vehicle = create_test_vehicle(customer, 'ABC-1234', 'Toyota', 'Corolla')
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
        vehicle = create_test_vehicle(customer, 'ABC-7777', 'Toyota', 'Camry')

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
        vehicle = create_test_vehicle(customer, 'ABC-1235', 'Honda', 'Civic')
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


class RelationalMappingTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='tester_relational', password='secret123')
        self.client.force_login(self.user)

        from fleet_app.models import Staff, StaffCategory
        from jobcard_app.models import ServiceCategory, SkillTag, ComplaintType, TechnicianSkill

        self.category = ServiceCategory.objects.create(name='Electrical System', description='Electrical repair')
        self.skill = SkillTag.objects.create(name='AC Diagnostics', description='AC skill tag')
        self.complaint_type = ComplaintType.objects.create(
            category=self.category,
            complaint_name='AC Compressor Noise',
            required_skill=self.skill
        )

        tech_cat, _ = StaffCategory.objects.get_or_create(name='Technician')
        self.technician = Staff.objects.create(
            staff_id='TECH-002',
            full_name='Master Technician',
            staff_category=tech_cat,
            status='Active',
            contact_number='123456'
        )

    def test_relational_mapping_ajax(self):
        response = self.client.get(reverse('jobcard_app:ajax_get_relational_mapping'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('categories', data)
        self.assertIn('technicians', data)
        self.assertIn('skills', data)

    def test_unqualified_technician_blocked_without_manual_override(self):
        customer = LedgerCreation.objects.create(ledger_name='Customer X')
        vehicle = create_test_vehicle(customer, 'REG-1001', 'Toyota', 'Corolla')

        response = self.client.post(reverse('jobcard_app:jobcard_create'), {
            'customer': customer.pk,
            'date': timezone.now().date().strftime('%Y-%m-%d'),
            'jc_vehicle_id[]': [vehicle.pk],
            'jc_vehicle_mileage[]': ['5000'],
            'jc_vehicle_fuel[]': ['1/2'],
            'jc_vehicle_notes[]': [''],
            'priority': 'normal',
            'status': 'open',
            'complaint_category_id[]': [str(self.category.pk)],
            'complaint_category[]': [self.category.name],
            'complaint_type_id[]': [str(self.complaint_type.pk)],
            'complaint_description[]': ['AC noise'],
            'complaint_type[]': [self.complaint_type.complaint_name],
            'complaint_technician[]': [str(self.technician.pk)],
            'complaint_status[]': ['Open'],
            'complaint_manual_override[]': ['0'],
        })

        self.assertEqual(response.status_code, 302)
        # JobCard should not have saved complaint due to validation error redirect
        self.assertEqual(JobCard.objects.count(), 0)

    def test_unqualified_technician_allowed_with_manual_override(self):
        customer = LedgerCreation.objects.create(ledger_name='Customer Y')
        vehicle = create_test_vehicle(customer, 'REG-1002', 'Honda', 'Civic')

        response = self.client.post(reverse('jobcard_app:jobcard_create'), {
            'customer': customer.pk,
            'date': timezone.now().date().strftime('%Y-%m-%d'),
            'jc_vehicle_id[]': [vehicle.pk],
            'jc_vehicle_mileage[]': ['5000'],
            'jc_vehicle_fuel[]': ['1/2'],
            'jc_vehicle_notes[]': [''],
            'priority': 'normal',
            'status': 'open',
            'complaint_category_id[]': [str(self.category.pk)],
            'complaint_category[]': [self.category.name],
            'complaint_type_id[]': [str(self.complaint_type.pk)],
            'complaint_description[]': ['AC noise'],
            'complaint_type[]': [self.complaint_type.complaint_name],
            'complaint_technician[]': [str(self.technician.pk)],
            'complaint_status[]': ['Open'],
            'complaint_manual_override[]': ['1'],
        })

        self.assertEqual(response.status_code, 302)
        job_card = JobCard.objects.order_by('-created_on').first()
        self.assertIsNotNone(job_card)
        complaint = job_card.complaints.first()
        self.assertIsNotNone(complaint)
        self.assertTrue(complaint.is_manual_override)
        self.assertEqual(complaint.technician, self.technician)

    def test_qualified_technician_allowed_without_override(self):
        from jobcard_app.models import TechnicianSkill
        TechnicianSkill.objects.create(technician=self.technician, skill=self.skill)

        customer = LedgerCreation.objects.create(ledger_name='Customer Z')
        vehicle = create_test_vehicle(customer, 'REG-1003', 'Nissan', 'Sunny')

        response = self.client.post(reverse('jobcard_app:jobcard_create'), {
            'customer': customer.pk,
            'date': timezone.now().date().strftime('%Y-%m-%d'),
            'jc_vehicle_id[]': [vehicle.pk],
            'jc_vehicle_mileage[]': ['5000'],
            'jc_vehicle_fuel[]': ['1/2'],
            'jc_vehicle_notes[]': [''],
            'priority': 'normal',
            'status': 'open',
            'complaint_category_id[]': [str(self.category.pk)],
            'complaint_category[]': [self.category.name],
            'complaint_type_id[]': [str(self.complaint_type.pk)],
            'complaint_description[]': ['AC noise'],
            'complaint_type[]': [self.complaint_type.complaint_name],
            'complaint_technician[]': [str(self.technician.pk)],
            'complaint_status[]': ['Open'],
            'complaint_manual_override[]': ['0'],
        })

        self.assertEqual(response.status_code, 302)
        job_card = JobCard.objects.order_by('-created_on').first()
        self.assertIsNotNone(job_card)
        complaint = job_card.complaints.first()
        self.assertIsNotNone(complaint)
        self.assertFalse(complaint.is_manual_override)
        self.assertEqual(complaint.technician, self.technician)

