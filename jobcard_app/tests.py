from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from item_master.models import Item, Unit
from accounts_app.models import Groups, LedgerCreation

from fleet_app.models import Staff, StaffCategory, Manufacturer, VehicleModel, VehicleCategory
from .models import WorkshopVehicle, VehicleInspection, InspectionFinding, ServiceCategory, JobCard


def create_test_customer(name='Test Customer'):
    group, _ = Groups.objects.get_or_create(pk=2, defaults={'groupName': 'Sundry Debtors'})
    return LedgerCreation.objects.create(ledger_name=name, groups=group)



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

        customer = create_test_customer('Test Customer')
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

        customer = create_test_customer('Test Customer')
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

        customer = create_test_customer('Test Customer')
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

        customer = create_test_customer('Test Customer')
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

        customer = create_test_customer('Test Customer')
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
        customer = create_test_customer('Customer X')
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
        customer = create_test_customer('Customer Y')
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

        customer = create_test_customer('Customer Z')
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


class ServiceTypeModuleTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='admin_tester', password='password123')
        self.client.force_login(self.user)
        from jobcard_app.models import ServiceCategory, SkillTag, ServiceType
        self.category = ServiceCategory.objects.create(name='Engine System', description='Engine repair category')
        self.skill = SkillTag.objects.create(name='Engine Tuning', description='Engine tuning skill tag')

    def test_service_type_crud(self):
        from jobcard_app.models import ServiceType
        # Create ServiceType
        response = self.client.post(reverse('jobcard_app:service_type_create'), {
            'category_id': self.category.id,
            'type_name': 'Oil & Filter Replacement',
            'code': 'SRV-OIL-01',
            'description': 'Full engine oil change',
            'required_skill_id': self.skill.id,
            'is_active': 'true',
        })
        self.assertEqual(response.status_code, 302)
        st = ServiceType.objects.filter(type_name='Oil & Filter Replacement').first()
        self.assertIsNotNone(st)
        self.assertEqual(st.category, self.category)
        self.assertEqual(st.required_skill, self.skill)

        # Parent category service_count
        self.assertEqual(self.category.service_count(), 1)

        # List view
        response = self.client.get(reverse('jobcard_app:service_type_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Oil &amp; Filter Replacement')

        # Edit ServiceType
        response = self.client.post(reverse('jobcard_app:service_type_edit', kwargs={'pk': st.pk}), {
            'category_id': self.category.id,
            'type_name': 'Engine Oil & Filter Service',
            'code': 'SRV-OIL-01-UPD',
            'description': 'Updated description',
            'required_skill_id': self.skill.id,
            'is_active': 'true',
        })
        self.assertEqual(response.status_code, 302)
        st.refresh_from_db()
        self.assertEqual(st.type_name, 'Engine Oil & Filter Service')

        # Delete ServiceType
        response = self.client.post(reverse('jobcard_app:service_type_delete', kwargs={'pk': st.pk}))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(ServiceType.objects.filter(pk=st.pk).exists())
        self.assertEqual(self.category.service_count(), 0)

    def test_staff_skill_tag_mapping(self):
        from fleet_app.models import Staff, StaffCategory
        from jobcard_app.models import SkillTag
        cat, _ = StaffCategory.objects.get_or_create(name='Technician')
        staff = Staff.objects.create(
            staff_id='TECH-999',
            full_name='Test Mechanic',
            staff_category=cat,
            status='Active',
        )
        staff.skills.add(self.skill)
        self.assertIn(self.skill, staff.skills.all())
        self.assertIn(staff, self.skill.staff_members.all())


class SkillTagMasterTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='admin_skill', password='password123')
        self.client.force_login(self.user)

    def test_skill_tag_crud(self):
        from jobcard_app.models import SkillTag
        # 1. List view
        response = self.client.get(reverse('jobcard_app:skill_tag_list'))
        self.assertEqual(response.status_code, 200)

        # 2. Create SkillTag
        response = self.client.post(reverse('jobcard_app:skill_tag_create'), {
            'name': 'Hybrid System Repair',
            'description': 'High voltage hybrid diagnostics',
            'is_active': True,
        })
        self.assertEqual(response.status_code, 302)
        tag = SkillTag.objects.filter(name='Hybrid System Repair').first()
        self.assertIsNotNone(tag)
        self.assertEqual(tag.description, 'High voltage hybrid diagnostics')

        # 3. Toggle Active status
        response = self.client.get(reverse('jobcard_app:skill_tag_toggle', kwargs={'pk': tag.pk}))
        self.assertEqual(response.status_code, 302)
        tag.refresh_from_db()
        self.assertFalse(tag.is_active)

        # 4. Edit SkillTag
        response = self.client.post(reverse('jobcard_app:skill_tag_edit', kwargs={'pk': tag.pk}), {
            'name': 'EV & Hybrid Diagnostics',
            'description': 'Electric vehicle & hybrid diagnostics',
            'is_active': True,
        })
        self.assertEqual(response.status_code, 302)
        tag.refresh_from_db()
        self.assertEqual(tag.name, 'EV & Hybrid Diagnostics')
        self.assertTrue(tag.is_active)

        # 5. Delete SkillTag
        response = self.client.post(reverse('jobcard_app:skill_tag_delete', kwargs={'pk': tag.pk}))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(SkillTag.objects.filter(pk=tag.pk).exists())


class InvoiceStockIntegrationTests(TestCase):
    def setUp(self):
        from accounts_app.models import LedgerCreation, Groups
        from item_master.models import Item, Unit, CostCenter
        from fleet_app.models import Vouchers
        from decimal import Decimal

        self.user = get_user_model().objects.create_user(username='inv_admin', password='password123')
        self.client.force_login(self.user)

        # Groups.groupId is a self-FK (parent group); None = top-level group
        self.group = Groups.objects.create(groupName='Sundry Debtors')
        self.customer = LedgerCreation.objects.create(ledger_name='Test Client Ltd', groups=self.group)

        self.unit = Unit.objects.create(unit_code='PCS', unit_name='Pcs')
        self.cost_center = CostCenter.objects.create(name='Main Workshop', code='WS-MAIN')
        self.item = Item.objects.create(
            item_name='Engine Oil 5W30',
            item_code='OIL-5W30',
            item_unit=self.unit,
            cost_center=self.cost_center,
            sales_rate=Decimal('50.00'),
        )
        self.voucher_type, _ = Vouchers.objects.get_or_create(
            VoucherType='Invoice',
            defaults={'VoucherName': 'Sales Invoice', 'Prefix': 'INV-', 'StartingNo': 1}
        )

    def test_invoice_creation_connects_item_master_and_reduces_stock(self):
        from jobcard_app.models import Invoice
        from item_master.models import Stock

        response = self.client.post(reverse('jobcard_app:invoice_create'), {
            'customer': self.customer.pk,
            'invoice_date': '2026-08-14',
            'status': 'sent',
            'payment_mode': 'cash',
            'part_item_id[]': [str(self.item.pk)],
            'part_name[]': [self.item.item_name],
            'part_code[]': [self.item.item_code],
            'part_qty[]': ['3'],
            'part_unit[]': ['Pcs'],
            'part_rate[]': ['50.00'],
            'part_disc[]': ['0'],
            'part_tax[]': ['8'],
        })
        self.assertEqual(response.status_code, 302)

        inv = Invoice.objects.order_by('-id').first()
        self.assertIsNotNone(inv)

        part = inv.parts.first()
        self.assertIsNotNone(part)
        self.assertEqual(part.item, self.item)
        self.assertEqual(part.get_item_obj(), self.item)

        stock_entry = Stock.objects.filter(item=self.item, voucherNo=inv.id).first()
        self.assertIsNotNone(stock_entry)
        self.assertEqual(stock_entry.out_quantity, 3)

    def test_invoice_update_adjusts_stock(self):
        from jobcard_app.models import Invoice, InvoicePart
        from item_master.models import Stock

        # Create invoice
        inv = Invoice.objects.create(
            customer=self.customer,
            invoice_date='2026-08-14',
            status='sent'
        )
        InvoicePart.objects.create(
            invoice=inv,
            item=self.item,
            item_ref=str(self.item.pk),
            item_code=self.item.item_code,
            description=self.item.item_name,
            quantity=2,
            unit_price=50,
        )
        from jobcard_app.views import _sync_invoice_stock
        _sync_invoice_stock(inv)

        stock_entry = Stock.objects.filter(item=self.item, voucherNo=inv.id).first()
        self.assertEqual(stock_entry.out_quantity, 2)

        # Update invoice with quantity 5
        response = self.client.post(reverse('jobcard_app:invoice_edit', kwargs={'pk': inv.pk}), {
            'customer': self.customer.pk,
            'invoice_date': '2026-08-14',
            'status': 'sent',
            'part_item_id[]': [str(self.item.pk)],
            'part_name[]': [self.item.item_name],
            'part_code[]': [self.item.item_code],
            'part_qty[]': ['5'],
            'part_unit[]': ['Pcs'],
            'part_rate[]': ['50.00'],
            'part_disc[]': ['0'],
            'part_tax[]': ['8'],
        })
        self.assertEqual(response.status_code, 302)

        stock_entry = Stock.objects.filter(item=self.item, voucherNo=inv.id).first()
        self.assertIsNotNone(stock_entry)
        self.assertEqual(stock_entry.out_quantity, 5)

    def test_invoice_deletion_reverts_stock(self):
        from jobcard_app.models import Invoice
        from item_master.models import Stock

        response = self.client.post(reverse('jobcard_app:invoice_create'), {
            'customer': self.customer.pk,
            'invoice_date': '2026-08-14',
            'status': 'sent',
            'part_item_id[]': [str(self.item.pk)],
            'part_name[]': [self.item.item_name],
            'part_code[]': [self.item.item_code],
            'part_qty[]': ['4'],
            'part_unit[]': ['Pcs'],
            'part_rate[]': ['50.00'],
        })
        inv = Invoice.objects.order_by('-id').first()
        self.assertTrue(Stock.objects.filter(item=self.item, voucherNo=inv.id).exists())

        # Delete invoice
        del_resp = self.client.post(reverse('jobcard_app:invoice_delete', kwargs={'pk': inv.pk}))
        self.assertEqual(del_resp.status_code, 302)

        self.assertFalse(Stock.objects.filter(item=self.item, voucherNo=inv.id).exists())

    def test_purchase_and_invoice_stock_calculation(self):
        from decimal import Decimal
        from jobcard_app.models import Invoice, InvoicePart
        from item_master.models import Stock, CostCenter
        from item_master.common import upsert_stock
        from fleet_app.models import Vouchers

        purch_vt = Vouchers.objects.filter(VoucherType__icontains='Purchase').first() or Vouchers.objects.first()
        cost_center = CostCenter.objects.first()

        # 1. Purchase 10 items
        upsert_stock(
            item=self.item,
            batch_id=None,
            base_unit_id=self.item.item_unit_id,
            base_qty_delta=Decimal('10'),
            rate=Decimal('100.00'),
            voucher_date=timezone.now().date(),
            voucher_type=purch_vt,
            voucher_id=999,
            cost_center=cost_center,
        )

        # Net stock should be 10
        stocks = Stock.objects.filter(item=self.item)
        net_qty = sum(s.in_quantity - s.out_quantity for s in stocks)
        self.assertEqual(net_qty, 10)

        # 2. Create Invoice with quantity 2
        inv = Invoice.objects.create(
            customer=self.customer,
            invoice_date=timezone.now().date(),
            status='sent'
        )
        InvoicePart.objects.create(
            invoice=inv,
            item=self.item,
            item_ref=str(self.item.pk),
            item_code=self.item.item_code,
            description=self.item.item_name,
            quantity=2,
            unit_price=100,
        )
        from jobcard_app.views import _sync_invoice_stock
        _sync_invoice_stock(inv)

        # Purchase record must still exist!
        purch_entry = Stock.objects.filter(item=self.item, voucherNo=999).first()
        self.assertIsNotNone(purch_entry)
        self.assertEqual(purch_entry.in_quantity, 10)

        # Total net stock must be 8 (10 in - 2 out)
        stocks = Stock.objects.filter(item=self.item)
        net_qty = sum(s.in_quantity - s.out_quantity for s in stocks)
        self.assertEqual(net_qty, 8)

        # 3. Re-sync/Update invoice
        _sync_invoice_stock(inv)
        purch_entry = Stock.objects.filter(item=self.item, voucherNo=999).first()
        self.assertIsNotNone(purch_entry)
        self.assertEqual(purch_entry.in_quantity, 10)

        stocks = Stock.objects.filter(item=self.item)
        net_qty = sum(s.in_quantity - s.out_quantity for s in stocks)
        self.assertEqual(net_qty, 8)





