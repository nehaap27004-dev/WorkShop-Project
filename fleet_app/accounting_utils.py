from decimal import Decimal
from django.db.models import Sum


from accounts_app.models import LedgerPosting, LedgerCreation, Groups


def _net(debit, credit):
    """Return debit − credit, treating None as zero."""
    return (debit or Decimal('0')) - (credit or Decimal('0'))


# ─────────────────────────────────────────────────────────────────────────────
# 2.  LEDGER BALANCE MAP
#     One DB query → dict  { ledger_id: net_movement }
# ─────────────────────────────────────────────────────────────────────────────

def get_ledger_balances(from_date, to_date):
    """
    Aggregate all LedgerPosting rows in [from_date, to_date].

    Returns:
        dict { ledger_id (int): net_movement (Decimal) }
        where  net_movement = total_debit − total_credit  for that ledger.

    Used by both build_sections() (Balance Sheet) and
    build_group_data() / build_group_total() (P&L).
    """
    qs = (
        LedgerPosting.objects
        .filter(date__gte=from_date, date__lte=to_date)
        .values('ledger_id')
        .annotate(
            total_debit=Sum('debit'),
            total_credit=Sum('credit'),
        )
    )
    return {
        row['ledger_id']: _net(row['total_debit'], row['total_credit'])
        for row in qs
    }


# ─────────────────────────────────────────────────────────────────────────────
# 3.  LEDGER BALANCE (single ledger)
#     Combines opening balance with period net, honouring DR / CR type.
# ─────────────────────────────────────────────────────────────────────────────

def calc_balance(led, ledger_balance):
    """
    Return the effective balance of a single ledger for the period.

    Logic:
        net_movement = ledger_balance[led.id]  (from get_ledger_balances)
        DR ledger:  balance = opening_balance + net_movement
        CR ledger:  balance = opening_balance − net_movement

    A positive result means the ledger is "active" on its natural side.
    A negative result means it has been over-reversed.

    Args:
        led            : LedgerCreation instance
        ledger_balance : dict from get_ledger_balances()

    Returns:
        Decimal
    """
    net_movement = ledger_balance.get(led.id, Decimal('0'))
    opening      = Decimal(str(led.opening_balance or 0))
    if led.types == 'DR':
        return opening + net_movement
    else:
        return opening - net_movement


# ─────────────────────────────────────────────────────────────────────────────
# 4.  GROUP DATA  (used by P&L view)
#     Full structure: group metadata + list of ledgers + child groups + total.
# ─────────────────────────────────────────────────────────────────────────────

def build_group_data(group_id, ledger_balance):
    """
    Build a display-ready data dict for one account group.

    Used by the P&L view for Purchase, Sales, Indirect Expense,
    Indirect Income — and any other group that needs a full breakdown.

    Args:
        group_id       : int  — primary key of the Groups record
        ledger_balance : dict from get_ledger_balances()

    Returns:
        {
          'group':        Groups instance,
          'ledgers':      [ {'ledger': LedgerCreation, 'balance': Decimal}, … ],
          'child_groups': [
              {
                'group':   Groups instance,
                'ledgers': [ {'ledger': LedgerCreation, 'balance': Decimal}, … ],
                'total':   Decimal,
              }, …
          ],
          'total':        Decimal,   # sum of all ledgers + child group totals
        }
        or None if the group does not exist.

    Note:
        Raw signed balances are returned (negative for CR-typed expense ledgers).
        Call normalize_for_display() afterwards if you need everything positive
        for on-screen rendering.
    """
    try:
        grp = Groups.objects.get(pk=group_id)
    except Groups.DoesNotExist:
        return None

    ledgers   = []
    grp_total = Decimal('0')

    # Direct ledgers under this group
    for led in LedgerCreation.objects.filter(groups=grp).order_by('ledger_name'):
        bal = calc_balance(led, ledger_balance)
        if bal != Decimal('0'):
            ledgers.append({'ledger': led, 'balance': bal})
            grp_total += bal

    # Child groups (one level deep)
    child_groups = []
    for child in Groups.objects.filter(groupId=grp).order_by('groupName'):
        child_total   = Decimal('0')
        child_ledgers = []
        for led in LedgerCreation.objects.filter(groups=child).order_by('ledger_name'):
            bal = calc_balance(led, ledger_balance)
            if bal != Decimal('0'):
                child_ledgers.append({'ledger': led, 'balance': bal})
                child_total += bal
        if child_total != Decimal('0'):
            child_groups.append({
                'group':   child,
                'ledgers': child_ledgers,
                'total':   child_total,
            })
            grp_total += child_total

    return {
        'group':        grp,
        'ledgers':      ledgers,
        'child_groups': child_groups,
        'total':        grp_total,
    }


# ─────────────────────────────────────────────────────────────────────────────
# 5.  GROUP TOTAL ONLY  (used by Balance Sheet's P&L injection)
#     Lighter version — no per-ledger list, just the signed sum.
# ─────────────────────────────────────────────────────────────────────────────

def build_group_total(group_id, ledger_balance):
    """
    Return the signed total for a group (direct ledgers + all child groups).

    Used by the Balance Sheet view when it only needs a number
    (purchase_total, sales_total, etc.) to compute net_profit —
    without building the full breakdown structure.

    Args:
        group_id       : int
        ledger_balance : dict from get_ledger_balances()

    Returns:
        Decimal  (signed — use abs() on the caller's side as needed)
    """
    try:
        grp = Groups.objects.get(pk=group_id)
    except Groups.DoesNotExist:
        return Decimal('0')

    total = Decimal('0')

    for led in LedgerCreation.objects.filter(groups=grp):
        total += calc_balance(led, ledger_balance)

    for child in Groups.objects.filter(groupId=grp):
        for led in LedgerCreation.objects.filter(groups=child):
            total += calc_balance(led, ledger_balance)

    return total


# ─────────────────────────────────────────────────────────────────────────────
# 6.  NORMALIZE FOR DISPLAY
#     Make all amounts positive in expense-nature groups.
# ─────────────────────────────────────────────────────────────────────────────

def normalize_for_display(group_data):
    """
    Convert all balances in a group_data dict to their absolute (positive) values.

    Call this AFTER all financial calculations are complete so that
    expense-group ledgers stored as CR type (which produce negative
    calc_balance results) display as positive amounts on screen.

    Mutates group_data in place.  Safe to call with None.

    Used by P&L for: Purchase, Indirect Expense.
    """
    if not group_data:
        return
    group_data['total'] = abs(group_data['total'])
    for item in group_data['ledgers']:
        item['balance'] = abs(item['balance'])
    for child in group_data['child_groups']:
        child['total'] = abs(child['total'])
        for item in child['ledgers']:
            item['balance'] = abs(item['balance'])