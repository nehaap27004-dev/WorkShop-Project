# Django Project Analysis: RABWA Accounting System

## Project Overview
This is a comprehensive Django-based ERP system combining accounting, fleet management, and inventory management functionalities. The project is designed for Arabic/English bilingual operations with PostgreSQL as the database backend.

---

## 1. INSTALLED APPS

### Core Applications:
1. **accounts_app** - Main accounting and financial management
2. **fleet_app** - Fleet/vehicle management system
3. **item_master** - Inventory and item management
4. **audit_app** - Audit trail functionality
5. **settings** - Global settings and currency management

### Django Built-in Apps:
- django.contrib.admin
- django.contrib.auth
- django.contrib.contenttypes
- django.contrib.sessions
- django.contrib.messages
- django.contrib.staticfiles

### Key Features:
- Multi-language support (English/Arabic) via django i18n
- PostgreSQL database backend
- Custom user authentication model
- Role-based access control system

---

## 2. MODEL RELATIONSHIPS

### 2.1 accounts_app Models

#### Authentication & Authorization Models:
```
CustomUser (extends AbstractUser)
    ├── ForeignKey: user_role → UserRole
    └── Fields: phone, address, place, isDefault

UserRole
    ├── Fields: name, is_admin
    └── Related: users, privileges

Menu
    ├── Fields: name, group, url
    └── Related: user_privileges

UserPrivilege
    ├── ForeignKey: user_role → UserRole
    ├── ForeignKey: menu → Menu
    └── Permissions: can_read, can_add, can_edit, can_cancel, can_delete,
        can_print, can_export, can_email, can_sms
    └── Constraint: unique_together(user_role, menu)
```

#### Chart of Accounts Hierarchy:
```
NatureOfGroup (Root level - Assets, Liabilities, etc.)
    └── MainGroup
        └── Group
            └── Subgroup
                └── LedgerCreation (Individual ledger accounts)
                    └── Related: payments, receipts, journal entries

Groups (Self-referencing hierarchy)
    ├── ForeignKey: groupId → self (parent group)
    └── Field: natureOfGroup (auto-calculated to root)
```

#### Transaction Models:

**Payment Module:**
```
PaymentMaster
    ├── ForeignKey: voucherType → fleet_app.Vouchers
    ├── ForeignKey: Ledger → LedgerCreation
    └── Related: PaymentDetails (multiple ledger entries)

PaymentBillMaster (Bill-wise payment clearance)
    ├── ForeignKey: Supplier → LedgerCreation
    ├── ForeignKey: Ledger → LedgerCreation (cash/bank)
    └── Related: PaymentBillDetails (cleared bills)
```

**Receipt Module:**
```
ReceiptMaster
    ├── ForeignKey: voucherType → fleet_app.Vouchers
    ├── ForeignKey: Ledger → LedgerCreation
    └── Related: ReceiptDetails (multiple ledger entries)

ReceiptBillMaster (Bill-wise receipt clearance)
    ├── ForeignKey: Customer → LedgerCreation
    ├── ForeignKey: Ledger → LedgerCreation (cash/bank)
    └── Related: ReceiptBillDetails (cleared bills)
```

**Local Payment (Expense Management):**
```
LocalPayment
    ├── ForeignKey: voucherType → fleet_app.Vouchers
    ├── ForeignKey: payment_mode → LedgerCreation
    └── Related:
        ├── LocalPaymentItems (line items with VAT)
        └── LocalPaymentCheque (cheque details)
```

**Journal Entries:**
```
Journal
    ├── ForeignKey: dr_ledger → LedgerCreation
    └── ForeignKey: cr_ledger → LedgerCreation

Contra
    ├── ForeignKey: dr_ledger → LedgerCreation
    └── ForeignKey: cr_ledger → LedgerCreation
```

**Ledger Posting (Consolidated ledger entries):**
```
LedgerPosting
    ├── ForeignKey: VoucherType → fleet_app.Vouchers
    ├── ForeignKey: ledger → LedgerCreation
    ├── ForeignKey: RefVoucherType → fleet_app.Vouchers
    ├── ForeignKey: CostCenter → item_master.CostCenter
    └── Fields: debit, credit, VoucherNo, RefVoucherNo
```

**Bill Clearance:**
```
BillClearance
    ├── ForeignKey: Ledger → LedgerCreation (party)
    ├── ForeignKey: Ledger2 → LedgerCreation (bank/cash)
    ├── ForeignKey: RefVoucherType → fleet_app.Vouchers
    ├── ForeignKey: Type → fleet_app.Vouchers (payment/receipt)
    └── Fields: InvAmount, Balance, Amount, PaymentMode
```

### 2.2 fleet_app Models

#### Master Data:
```
Company
    └── Related: CompanyDocument, quotations

Manufacturer
    └── Related: VehicleModel, RentalCompanyVehicle

VehicleCategory
    └── Related: VehicleModel, Vehicle

VehicleModel
    ├── ForeignKey: manufacturer → Manufacturer
    ├── ForeignKey: vehicle_category → VehicleCategory
    └── Related: Vehicle

LicensePlateCode
    └── Related: Vehicle
```

#### Staff & Driver Management:
```
StaffCategory
    └── Related: Staff

Staff
    ├── ForeignKey: staff_category → StaffCategory
    └── Related: vehicles (as driver), timesheets, contracts
    └── Fields: Complete HR info (salary, visa, license, etc.)

Driver (External drivers)
    ├── ForeignKey: driver_company → RentalCompany
    └── Related: RentalCompanyVehicle
```

#### Vehicle Management:
```
Vehicle (Own vehicles)
    ├── ForeignKey: model → VehicleModel
    ├── ForeignKey: license_plate_code → LicensePlateCode
    ├── ForeignKey: vehicle_driver → Staff
    ├── ForeignKey: vehicle_second_driver → Staff
    ├── ForeignKey: vehicle_category → VehicleCategory
    ├── ForeignKey: supplier → LedgerCreation (if rented)
    └── Fields: is_owned, rates (per hr/day/week/month/year)
    └── Related: hire_details, invoices, quotation_items

RentalCompanyVehicle (Supplier vehicles)
    ├── ForeignKey: company → LedgerCreation
    ├── ForeignKey: vehicle_driver → Driver
    ├── ForeignKey: vehicle_manufacturer → Manufacturer
    ├── ForeignKey: vehicle_model → VehicleModel
    └── Related: Similar to Vehicle
```

#### Vouchers System:
```
Vouchers (Voucher numbering system)
    ├── ForeignKey: ledger → LedgerCreation
    └── Fields: VoucherType, Prefix, Suffix, StartingNo, MinLength
    └── Method: get_next_voucher_number() - Auto-generates voucher numbers
```

#### Operations:
```
FleetHire (Hire-in from suppliers)
    ├── ForeignKey: voucherType → Vouchers
    ├── ForeignKey: supplier → LedgerCreation
    └── Related: FleetHireDetails
        ├── ForeignKey: vehicle → Vehicle
        └── Fields: start_date, end_date, unit, rate

Invoice (Hire-out to customers)
    ├── ForeignKey: voucherType → Vouchers
    ├── ForeignKey: customer → LedgerCreation
    └── Related: InvoiceDetails
        ├── ForeignKey: vehicle → Vehicle
        └── Fields: amount, tax, total_amount

FleetContract
    ├── ForeignKey: voucherType → Vouchers
    ├── ForeignKey: vehicle → Vehicle
    ├── ForeignKey: operator_1 → Staff
    └── ForeignKey: customer → LedgerCreation

TimeSheet
    ├── ForeignKey: voucherType → Vouchers
    ├── ForeignKey: vehicle_name → Vehicle
    ├── ForeignKey: client → LedgerCreation
    ├── ForeignKey: driver_name → Staff
    ├── ForeignKey: operator_name → Staff
    └── Related: TimeSheetDetail (daily entries)
```

#### Quotations:
```
SimpleQuotation
    ├── ForeignKey: voucherType → Vouchers
    ├── ForeignKey: customer → LedgerCreation
    └── Related: SimpleQuotationDetails

FleetQuotation
    ├── ForeignKey: company_name → Company
    ├── ForeignKey: customer → LedgerCreation
    └── Related: FleetQuotationItem
        └── ForeignKey: vehicle → Vehicle
```

#### Maintenance:
```
RepairAndMaintenance
    ├── ForeignKey: voucherType → Vouchers
    ├── ForeignKey: vehicle_name → Vehicle
    ├── ForeignKey: vehicle_driver → Staff
    └── Related: RepairAndMaintenanceItem
```

### 2.3 item_master Models

#### Master Data:
```
CostCenter
    └── Related: Items, Stock, Vouchers

ItemCategory
    └── Related: Items

ItemManufacturer
    └── Related: Items

Unit
    └── Related: Items, ItemAlterUnit, Stock

TAX
    └── Related: Items

Batch
    ├── ForeignKey: Item → Item
    └── Related: Stock, PurchaseDetail, SalesDetail
```

#### Item Management:
```
Item
    ├── ForeignKey: item_category → ItemCategory
    ├── ForeignKey: item_manufacturer → ItemManufacturer
    ├── ForeignKey: TAX → TAX
    ├── ForeignKey: item_unit → Unit
    ├── ForeignKey: cost_center → CostCenter
    └── Related:
        ├── ItemAlterUnit (alternate units)
        ├── Batch (batch tracking)
        └── Stock entries

ItemAlterUnit
    ├── ForeignKey: item → Item
    └── ForeignKey: unit → Unit
```

#### Purchase Module:
```
PurchaseMaster
    ├── ForeignKey: voucherType → Vouchers
    ├── ForeignKey: ledger → LedgerCreation (supplier)
    ├── ForeignKey: cost_center → CostCenter
    └── Related: PurchaseDetail
        ├── ForeignKey: item_name → Item
        ├── ForeignKey: unit → Unit
        ├── ForeignKey: Batch → Batch
        └── ForeignKey: BaseUnit → Unit

PurchaseReturnMaster
    └── Similar structure to PurchaseMaster
```

#### Sales Module:
```
SalesMaster
    ├── ForeignKey: voucherType → Vouchers
    ├── ForeignKey: ledger → LedgerCreation (customer)
    ├── ForeignKey: cost_center → CostCenter
    └── Related: SalesDetail
        ├── ForeignKey: item_name → Item
        ├── ForeignKey: unit → Unit
        ├── ForeignKey: Batch → Batch
        └── ForeignKey: BaseUnit → Unit

SalesReturnMaster
    └── Similar structure to SalesMaster
```

#### Stock Management:
```
Stock
    ├── ForeignKey: voucherType → Vouchers
    ├── ForeignKey: item → Item
    ├── ForeignKey: batch → Batch
    ├── ForeignKey: unit → Unit
    ├── ForeignKey: costCenter → CostCenter
    └── Fields: in_quantity, out_quantity, stock_value

StockTransfer
    ├── ForeignKey: voucherType → Vouchers
    ├── ForeignKey: source_cost_center → CostCenter
    ├── ForeignKey: destination_cost_center → CostCenter
    └── Related: StockTransferItem
        ├── ForeignKey: item → Item
        ├── ForeignKey: unit → Unit
        └── ForeignKey: batch → Batch

OpeningStockMaster
    ├── ForeignKey: ledger → LedgerCreation
    ├── ForeignKey: cost_center → CostCenter
    └── Related: OpeningStockDetail
```

#### Reporting:
```
OutstandingReport
    ├── ForeignKey: ledger → LedgerCreation
    └── Related: BillByBill (settlement tracking)

DayBookReport
    └── Fields: date, ledger, voucher_type, amounts
```

### 2.4 settings Models

```
GlobalSettings (Singleton configuration)
    └── Fields: System-wide settings
        ├── update_rate_from_purchase
        ├── billbybill
        ├── costcenter
        ├── negative_stock (Allow/Warning/Block)
        ├── credit_limit (Allow/Warning/Block)
        └── barcode settings

Currency
    └── Fields: CurrencyName, Decimal, MajorSymbol, MinorSymbol
```

---

## 3. MAIN WORKFLOWS

### 3.1 Payment Workflow

**Process Flow:**
1. User creates Payment/Receipt (PaymentMaster/ReceiptMaster)
2. Multiple ledger entries added (PaymentDetails/ReceiptDetails)
3. System creates LedgerPosting entries for each transaction
4. For credit transactions:
   - Bill clearance tracked in PaymentBillMaster/ReceiptBillMaster
   - Outstanding updated in OutstandingReport
5. Voucher number auto-generated via Vouchers.get_next_voucher_number()

**Bill Clearance:**
```
Invoice/FleetHire (Credit) → Outstanding Balance
    ↓
PaymentBillMaster/ReceiptBillMaster created
    ↓
PaymentBillDetails/ReceiptBillDetails (link to original bills)
    ↓
BillClearance records created
    ↓
Invoice.IsCleared = True (when fully paid)
```

### 3.2 Fleet Management Workflow

**Vehicle Hire-In (from suppliers):**
```
FleetHire created
    ├── Supplier: LedgerCreation (supplier)
    ├── FleetHireDetails: Multiple vehicles
    └── Creates LedgerPosting (Dr: Expense, Cr: Supplier)
```

**Vehicle Hire-Out (to customers):**
```
Invoice created
    ├── Customer: LedgerCreation (customer)
    ├── InvoiceDetails: Multiple vehicles
    └── Creates LedgerPosting (Dr: Customer, Cr: Income)
```

**Quotation → Invoice:**
```
SimpleQuotation/FleetQuotation → Customer approval → Invoice
```

**Timesheet Workflow:**
```
TimeSheet created
    ├── Vehicle assignment
    ├── Driver/Operator assignment
    └── TimeSheetDetail: Daily time tracking
        └── Used for billing/payroll
```

### 3.3 Purchase & Sales Workflow

**Purchase Flow:**
```
PurchaseMaster created
    ├── Supplier: LedgerCreation
    ├── PurchaseDetail: Multiple items
    └── Triggers:
        ├── Stock entry (in_quantity)
        ├── LedgerPosting (Dr: Purchase, Cr: Supplier)
        └── If cash/bank: Creates Payment entry
```

**Sales Flow:**
```
SalesMaster created
    ├── Customer: LedgerCreation
    ├── SalesDetail: Multiple items
    └── Triggers:
        ├── Stock entry (out_quantity)
        ├── LedgerPosting (Dr: Customer, Cr: Sales)
        └── If cash/bank: Creates Receipt entry
```

**Stock Management:**
```
All transactions update Stock table:
    ├── Purchase/Opening Stock → in_quantity
    ├── Sales/Production → out_quantity
    └── Stock Transfer between CostCenters
```

### 3.4 Voucher Numbering System

**Centralized Voucher Management:**
```
Vouchers model manages all document numbering:
    ├── Prefix (e.g., "INV", "PY")
    ├── Suffix (e.g., "/24")
    ├── MinLength (zero-padding, default: 5)
    ├── StartingNo (default: 1)
    └── get_next_voucher_number() method
        └── Scans all models using this voucher type
        └── Returns: "INV00001/24", "PY00002/24"

Usage in models:
def save(self, *args, **kwargs):
    if not self.voucher_no and self.voucherType:
        self.voucher_no = self.voucherType.get_next_voucher_number()
    super().save(*args, **kwargs)
```

### 3.5 Accounting Integration

**Double Entry System:**
Every transaction creates LedgerPosting entries:
```
Invoice (Customer billing):
    Dr: Customer Account (LedgerCreation)
    Cr: Sales Account (from Vouchers.ledger)

Payment (Paying supplier):
    Dr: Supplier Account
    Cr: Bank/Cash Account

LocalPayment (Expenses):
    Dr: Expense Ledgers (multiple)
    Cr: Bank/Cash Account
```

---

## 4. AUTHENTICATION SYSTEM

### 4.1 Custom User Model

**CustomUser (extends AbstractUser):**
```python
AUTH_USER_MODEL = 'accounts_app.CustomUser'

Fields:
    ├── username, email, password (inherited)
    ├── user_role → ForeignKey to UserRole
    ├── phone, address, place
    └── Timestamps: created_on, updated_on
    └── Tracking: created_by, updated_by
```

### 4.2 Login/Logout Implementation

**Login Process:**
```python
# accounts_app/views.py
def admin_login(request):
    if request.user.is_authenticated:
        # Redirect if already logged in
    
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        
        if user:
            login(request, user)
            # Check user role and redirect accordingly
        else:
            # Show error message

@login_required(login_url='accounts_app:admin_login')
def protected_view(request):
    # View logic
```

**Logout:**
```python
def logout_view(request):
    logout(request)
    return redirect('accounts_app:admin_login')
```

### 4.3 Session Management

- Django's built-in session middleware
- Session stored in database
- Login required decorator protects views
- Automatic redirect to login page for unauthenticated users

---

## 5. PERMISSIONS SYSTEM

### 5.1 Role-Based Access Control (RBAC)

**Architecture:**
```
User → UserRole → UserPrivilege → Menu
                      ↓
                  Permissions Matrix
```

### 5.2 Permission Levels

**UserPrivilege Model:**
```python
Granular permissions per menu item:
    ├── can_read: View access
    ├── can_add: Create new records
    ├── can_edit: Modify existing records
    ├── can_cancel: Cancel/void transactions
    ├── can_delete: Delete records
    ├── can_print: Print documents
    ├── can_export: Export data
    ├── can_email: Send emails
    └── can_sms: Send SMS

Constraint: unique_together(user_role, menu)
```

### 5.3 Permission Checking

**Template Tag Usage:**
```django
{% load privilege_tags %}

{% if has_priv user menu_id "can_read" %}
    <!-- Show content -->
{% endif %}

{% if has_priv user menu_id "can_add" %}
    <a href="{% url 'create_form' %}">Add New</a>
{% endif %}
```

**Backend Implementation:**
```python
# accounts_app/common.py
def check_privilege(user, menu_ids, privilege_fields):
    """
    Check if user has specified privileges for menu(s)
    
    Args:
        user: Current user object
        menu_ids: int or list of menu IDs
        privilege_fields: str or list of permission names
    
    Returns:
        bool: True if user has ANY of the specified privileges
    """
    
    # Superuser bypass
    if user.is_superuser:
        return True
    
    # Get user's role
    role = user.user_role
    
    # Query UserPrivilege
    privileges = UserPrivilege.objects.filter(
        user_role=role, 
        menu_id__in=menu_ids
    )
    
    # Check if any privilege matches
    for privilege in privileges:
        for field in privilege_fields:
            if getattr(privilege, field, False):
                return True
    
    return False
```

### 5.4 Menu System

**Menu Model:**
```python
Menu:
    ├── name: Display name
    ├── group: Menu grouping (Accounts, Fleet, etc.)
    └── url: URL path for matching

Usage:
    ├── Dynamic menu generation based on user privileges
    ├── URL-based permission checking
    └── Menu items visible only if user has can_read permission
```

### 5.5 Admin vs Regular Users

**UserRole:**
```python
UserRole:
    └── is_admin: Boolean flag
        ├── True: Full system access (like superuser)
        └── False: Restricted by UserPrivilege settings
```

**Permission Hierarchy:**
```
1. Superuser (user.is_superuser = True)
   └── Complete access, bypasses all checks

2. Admin Role (user_role.is_admin = True)
   └── Full access to assigned features

3. Regular Users
   └── Access based on UserPrivilege settings per menu
```

### 5.6 Audit Trail

**Tracking Fields (in most models):**
```python
created_on = models.DateTimeField(auto_now_add=True)
updated_on = models.DateTimeField(auto_now=True)
created_by = models.IntegerField(null=True, blank=True)  # User ID
updated_by = models.IntegerField(null=True, blank=True)  # User ID
```

**audit_app:**
- Configured to auto-audit specified apps
- AUDITLOG_INCLUDE_APPS = ["accounts_app", "fleet_app", "item_master"]

---

## 6. KEY FEATURES

### 6.1 Multi-Currency Support
- Currency master with configurable decimal places
- Major/Minor symbols for display

### 6.2 Multi-Language Support
- English and Arabic languages
- LocaleMiddleware for dynamic language switching
- Translation files in locale/ar/LC_MESSAGES/

### 6.3 VAT/Tax Management
- Multiple tax rates supported
- VAT types: No VAT, Inclusive, Exclusive
- Automatic tax calculation in transactions

### 6.4 Document Management
- File uploads for vehicles, staff, companies
- Document tracking with expiry dates
- Reminder system for document renewals

### 6.5 Cheque Management
- PDC (Post Dated Cheque) tracking
- Cheque status: Pending, Cleared, Bounced, Cancelled
- Bounce charges handling

### 6.6 Cost Center Tracking
- Multi-location/department tracking
- Stock transfer between cost centers
- Cost center-wise profitability

### 6.7 Batch & Serial Number Tracking
- Batch number management
- Manufacture and expiry date tracking
- Serial number tracking for specific items

---

## 7. DATABASE SCHEMA HIGHLIGHTS

### Key Relationships:
1. **LedgerCreation** is the central hub for all parties (customers, suppliers, employees)
2. **Vouchers** manages document numbering across all modules
3. **LedgerPosting** consolidates all accounting entries
4. **CostCenter** enables multi-location operations
5. **Vehicle** connects fleet operations to accounting

### Data Integrity:
- Foreign key constraints throughout
- Unique constraints on voucher numbers
- Cascade deletes configured appropriately
- Audit trails on all transactional data

---

## 8. REPORTS & ANALYTICS

### Available Reports:
1. **DayBook**: Daily transaction summary
2. **Ledger**: Account-wise transaction history
3. **Outstanding**: Receivables/Payables tracking
4. **Stock**: Inventory valuation and movement
5. **Timesheet**: Employee/vehicle utilization
6. **Bill Clearance**: Payment settlement tracking

---

## 9. TECHNOLOGY STACK

- **Backend**: Django 5.0.7
- **Database**: PostgreSQL
- **Frontend**: Django Templates (with i18n support)
- **Authentication**: Django built-in + Custom RBAC
- **File Storage**: Local filesystem (MEDIA_ROOT)
- **Static Files**: Collected in staticfiles/

---

## 10. SECURITY CONSIDERATIONS

### Implemented:
✅ Custom user model with role-based access
✅ Granular permission system
✅ Login required decorators
✅ Superuser bypass for admin tasks
✅ Audit trail (created_by, updated_by)
✅ CSRF protection (Django middleware)
✅ SQL injection protection (Django ORM)

### Recommendations:
⚠️ SECRET_KEY is exposed (should use environment variable)
⚠️ DEBUG=True in production (should be False)
⚠️ ALLOWED_HOSTS is empty (should specify domains)
⚠️ Consider implementing API rate limiting
⚠️ Add password reset functionality
⚠️ Implement 2FA for sensitive operations

---

## CONCLUSION

This is a well-structured, feature-rich ERP system that combines:
- **Accounting**: Full double-entry bookkeeping with bill clearance
- **Fleet Management**: Vehicle tracking, hire-in/hire-out, timesheets
- **Inventory**: Purchase, sales, stock management with batch tracking
- **RBAC**: Comprehensive role-based permissions system
- **Reporting**: Multiple financial and operational reports

The system demonstrates good Django practices with proper model relationships, custom managers, and a centralized voucher numbering system. The permission system is particularly robust with granular control at the menu level.
