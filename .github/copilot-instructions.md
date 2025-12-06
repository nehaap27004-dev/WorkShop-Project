# AI Agent Instructions for RABWA Accounting System

## Project Overview
Django 5.0 ERP accounting system with fleet management. Multi-app architecture: `accounts_app` (core ledger), `fleet_app` (vehicles/hirings), `item_master` (inventory), `audit_app`, and `settings` (configuration). PostgreSQL backend.

## Architecture Patterns

### Custom User Model
- **Override**: Django's default User is replaced with `CustomUser` (extends `AbstractUser`) in `accounts_app/models.py`
- **Critical**: Always import from `accounts_app.models` not `django.contrib.auth.models`
- **Settings**: `AUTH_USER_MODEL = 'accounts_app.CustomUser'` in `accounts/settings.py`
- Fields: `user_role` (FK), `phone`, `address`, `place`, `isDefault`, `created_on/by`, `updated_on/by`

### Role-Based Access Control (RBAC)
- **Models**: `UserRole`, `Menu`, `UserPrivilege` define granular permissions
- **Privilege check function**: `check_privilege(user, menu_ids, privilege_fields)` in `accounts_app/common.py`
  - Accepts single int or list of menu IDs
  - Privilege fields: `can_read`, `can_add`, `can_edit`, `can_cancel`, `can_delete`, `can_print`, `can_export`, `can_email`, `can_sms`
  - **Superusers bypass all checks** automatically
- **Usage**: `if check_privilege(request.user, menu_id, "can_edit"): ...`

### Accounting Core: Hierarchical Chart of Accounts
- **Hierarchy**: `NatureOfGroup` → `MainGroup` → `Group` → `Subgroup` → `LedgerCreation`
- **Auto-numbering**: Models save with sequential `_no` fields (e.g., `main_group_no`, `group_no`)
- **Self-referential**: `Groups` model has optional `groupId` FK to itself for subnesting
- **Default tracking**: Most models have `isDefault` boolean for system defaults

### Double-Entry Bookkeeping
- **Core tables**: `Journal`, `LedgerPosting`, `BillClearance`, `Payment`, `Receipt`
- **LedgerPosting** (line-item ledger): Stores debit/credit for every voucher
  - FK to `LedgerCreation` (account), `Vouchers` (voucher type), `CostCenter` (optional)
  - Fields: `date`, `VoucherType`, `VoucherNo`, `debit`, `credit`, `RefVoucherNo`, `RefVoucherType`, `IsDeleted`, `FY` (fiscal year)
- **BillClearance**: Partial/full payment reconciliation against invoices
  - Tracks `RefVoucherNo` (original invoice), `Amount` (payment), `Balance`, payment mode (cash/bank)
  - Optional cheque details with status (`pending`, `cleared`, `bounced`, `cancelled`)

### Cross-App Integration Points
1. **fleet_app ↔ accounts_app**: 
   - `Vouchers` table defines all document types (Payment=3, Receipt, Hire, etc.)
   - `fleet_app.common` has ledger posting creation functions:
     - `create_ledger_postings_for_payment()`, `create_ledger_postings_for_receipt()`
     - `create_bounce_charge_ledger_posting()` for cheque bounces
   - Import at top of accounts_app views: `from fleet_app.common import create_ledger_postings_for_*`
2. **item_master ↔ accounts_app**:
   - `CostCenter` (cost allocation), `TAX`, `Unit`, `ItemCategory` used in transactions
3. **settings ↔ all apps**:
   - Global context processor in `settings/context_processors.py`
   - Registered in settings.py TEMPLATES['OPTIONS']['context_processors']

## Conventions & Patterns

### Timestamp & Audit Fields
- **All models** include: `created_on`, `updated_on` (auto_now_add/auto_now), `created_by`, `updated_by` (IntegerField, nullable)
- Pattern in views: `obj.created_by = request.user.id` before save

### Form & Formset Patterns
- HTML forms use Bootstrap class `form-control` on all inputs
- Use `modelformset_factory()` and `inlineformset_factory()` for related objects
- Formsets in templates use loop: `{% for form in formset %}...{% endfor %}`
- Always validate `formset.is_valid()` AND check individual form errors

### Data Import Scripts
- CSV imports use `psycopg2` direct connection in app root: `accounts_app/import_ledger.py`, `import_groups.py`
- DB credentials hardcoded (NOT production-safe); change before production
- Use `INSERT ... ON CONFLICT (id) DO NOTHING` for idempotency

### Privilege-Guarded Views
- Prefix views with `@login_required(login_url='accounts_app:admin_login')`
- Add privilege check after: `if not check_privilege(request.user, MENU_ID, "can_edit"): return HttpResponseForbidden(...)`
- Alternative: Use `@never_cache` decorator for sensitive pages like login

### Decimal Precision
- **All monetary fields**: `DecimalField(max_digits=15, decimal_places=3)` (allows values up to 999,999,999.999)
- Critical in calculations: Use `from decimal import Decimal` to avoid float precision loss

## Development Workflow

### Database Setup
```bash
# Migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Import seed data (if needed)
python accounts_app/import_ledger.py
python accounts_app/import_groups.py
```

### Running Dev Server
```bash
python manage.py runserver
```

### Creating Models/Fields
- Run migrations after model changes: `python manage.py makemigrations && python manage.py migrate`
- Check `accounts_app/migrations/` for pattern (16+ existing migrations show convention)

### Common View Patterns in codebase

**Formset handling** (from `accounts_app/views.py`):
```python
@login_required
def journal_create(request):
    if request.method == 'POST':
        form = JournalForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.created_by = request.user.id
            obj.save()
            return redirect('accounts_app:journal_list')
    else:
        form = JournalForm()
    return render(request, 'journal_form.html', {'form': form})
```

**Inline formsets**:
```python
ItemFormSet = inlineformset_factory(Invoice, InvoiceItem, form=ItemForm, extra=1)
if request.POST:
    formset = ItemFormSet(request.POST, instance=invoice)
    if formset.is_valid():
        formset.save()
```

## Key Files to Reference

| Component | Files |
|-----------|-------|
| **Auth & Privileges** | `accounts_app/models.py` (CustomUser, UserRole, UserPrivilege), `accounts_app/common.py` (check_privilege) |
| **Chart of Accounts** | `accounts_app/models.py` (Groups, MainGroup, LedgerCreation) |
| **Ledger & Posting** | `accounts_app/models.py` (LedgerPosting, BillClearance, Payment) |
| **Fleet Integration** | `fleet_app/models.py` (Vouchers), `fleet_app/common.py` (ledger posting functions) |
| **Forms** | `accounts_app/forms.py` (700+ lines; formsets for all major models) |
| **Views** | `accounts_app/views.py` (1900+ lines; comprehensive CRUD patterns) |
| **Settings** | `accounts/settings.py` (Django 5.0 config, PostgreSQL, installed apps) |
| **URLs** | Root in `accounts/urls.py`, per-app in `*/urls.py` with namespace routing |

## Critical DO's & DON'Ts

✅ **DO:**
- Always check user privileges before CRUD operations
- Use `Decimal` for financial calculations
- Create ledger postings via fleet_app functions when recording payments/receipts
- Track `created_by` and `updated_by` on every model save
- Use `@login_required` on all sensitive views
- Validate formsets with `is_valid()` before processing

❌ **DON'T:**
- Import User from `django.contrib.auth.models` (use `CustomUser` from `accounts_app.models`)
- Use float for money (always Decimal)
- Create LedgerPosting entries manually; use helper functions in `fleet_app/common.py`
- Forget audit trail fields (`created_by`, `updated_by`, timestamps)
- Mix DB credential sources; keep them centralized in settings.py or environment variables

## Testing & Debugging
- Test views with `@login_required`: Use `request.user` fixtures in tests
- Privilege testing: Mock `UserPrivilege` objects with specific `user_role` and menu IDs
- DB queries: Enable query logging in settings for N+1 detection (use `select_related()`, `prefetch_related()`)
