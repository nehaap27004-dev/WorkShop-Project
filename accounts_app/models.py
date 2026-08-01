from django.db import models
from django.utils import timezone
from decimal import Decimal
from django.db import models
from django.contrib.auth.models import AbstractUser
import fleet_app
from item_master.models import CostCenter

class UserRole(models.Model):
    name = models.CharField(max_length=100, unique=True)
    is_admin = models.BooleanField(default=False)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    created_by = models.IntegerField(null=True, blank=True)   
    updated_by = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return self.name


class Menu(models.Model):
    name = models.CharField(max_length=100)
    group = models.CharField(max_length=100, blank=True, null=True)
    url = models.CharField(max_length=255, blank=True, null=True)
    
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    created_by = models.IntegerField(null=True, blank=True)   
    updated_by = models.IntegerField(null=True, blank=True)
    

    def __str__(self):
        return f"{self.group} - {self.name}" if self.group else self.name


class UserPrivilege(models.Model):
    user_role = models.ForeignKey(UserRole, on_delete=models.PROTECT)
    menu = models.ForeignKey(Menu, on_delete=models.PROTECT)

    can_read = models.BooleanField(default=False)
    can_add = models.BooleanField(default=False)
    can_edit = models.BooleanField(default=False)
    can_cancel = models.BooleanField(default=False)
    can_delete = models.BooleanField(default=False)
    can_print = models.BooleanField(default=False)
    can_export = models.BooleanField(default=False)
    can_email = models.BooleanField(default=False)
    can_sms = models.BooleanField(default=False)
    
    isDefault = models.BooleanField(default=False)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    created_by = models.IntegerField(null=True, blank=True)   
    updated_by = models.IntegerField(null=True, blank=True)

    class Meta:
        unique_together = ('user_role', 'menu')

    def __str__(self):
        return f"{self.user_role} - {self.menu}"
    
class CustomUser(AbstractUser):
    user_role = models.ForeignKey('UserRole', on_delete=models.SET_NULL, null=True, blank=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True, max_length=1000)
    place = models.CharField(max_length=255, blank=True, null=True)
    isDefault = models.BooleanField(default=False)
    
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    created_by = models.IntegerField(null=True, blank=True)   
    updated_by = models.IntegerField(null=True, blank=True)
    

    def __str__(self):
        return self.username    
    
    
class Groups(models.Model):
    groupName = models.CharField(max_length=100)
    group_desc = models.TextField(blank=True, null=True)
    groupId = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='subgroups')
    natureOfGroup = models.PositiveIntegerField(blank=True, null=True)
    isDefault = models.BooleanField(default=False)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    
    created_by = models.IntegerField(null=True, blank=True)   
    updated_by = models.IntegerField(null=True, blank=True)

    def save(self, *args, **kwargs):
        # Set natureOfGroup to root ancestor ID
        if self.groupId:
            root = self.groupId
            while root.groupId:
                root = root.groupId
            self.natureOfGroup = root.id
        else:
            self.natureOfGroup = self.id if self.id else None  # will set after first save
        super().save(*args, **kwargs)
        if not self.natureOfGroup:
            self.natureOfGroup = self.id
            super().save(update_fields=['natureOfGroup'])

    def __str__(self):
        return self.groupName


class NatureOfGroup(models.Model):
    nature_of_group_name = models.CharField(max_length=255, unique=True)
    nature_of_group_description = models.TextField(blank=True, null=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    
    
    
    
    def __str__(self):
        return self.nature_of_group_name

class MainGroup(models.Model):
    main_group_no = models.PositiveIntegerField(unique=True, editable=False)
    main_group_name = models.CharField(max_length=255, unique=True)
    main_group_description = models.TextField(blank=True, null=True)
    nature_of_group = models.ForeignKey(NatureOfGroup, on_delete=models.PROTECT, related_name='main_groups')
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        if not self.pk:  # Only set group_no for new objects
            # Set group_no to the next available number
            max_main_group_no = MainGroup.objects.aggregate(max_no=models.Max('main_group_no'))['max_no']
            self.main_group_no = (max_main_group_no or 0) + 1
        super().save(*args, **kwargs)

    def __str__(self):
        return self.main_group_name

# Group Model
class Group(models.Model):
    group_no = models.PositiveIntegerField(unique=True, editable=False)
    group_name = models.CharField(max_length=255)
    group_description = models.TextField(blank=True, null=True)
    main_group = models.ForeignKey(MainGroup, on_delete=models.PROTECT, related_name='groups')
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        if not self.pk:  # Only set group_no for new objects
            # Set group_no to the next available number
            max_group_no = Group.objects.aggregate(max_no=models.Max('group_no'))['max_no']
            self.group_no = (max_group_no or 0) + 1
        super().save(*args, **kwargs)
    



    def __str__(self):
        return self.group_name
    
class GroupUnder(models.Model):
    under_name = models.CharField(max_length=100)
    main_group = models.ForeignKey(MainGroup, on_delete=models.PROTECT, null=True, blank=True)
    group = models.ForeignKey(Group, on_delete=models.PROTECT, null=True, blank=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.under_name    

# Subgroup Model
class Subgroup(models.Model):
    sub_group_no = models.PositiveIntegerField(unique=True, editable=False)
    sub_group_name = models.CharField(max_length=255)
    sub_group_description = models.TextField(blank=True, null=True)
    isDefault = models.BooleanField(default=False)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    
    created_by = models.IntegerField(null=True, blank=True)   
    updated_by = models.IntegerField(null=True, blank=True)
    
    def save(self, *args, **kwargs):
        if not self.pk:  # Only set group_no for new objects
            # Set group_no to the next available number
            max_sub_group_no = Subgroup.objects.aggregate(max_no=models.Max('sub_group_no'))['max_no']
            self.sub_group_no = (max_sub_group_no or 0) + 1
        super().save(*args, **kwargs)

    def __str__(self):
        return self.sub_group_name

# LedgerCreation Model
class LedgerCreation(models.Model):
    DR_CR_CHOICES = [
        ('DR', 'Dr'),
        ('CR', 'Cr'),
    ]
    ledger_name = models.CharField(max_length=255)
    groups = models.ForeignKey(Groups, on_delete=models.PROTECT, related_name='ledgers',blank=True, null=True)
    sub_group = models.ForeignKey(Subgroup, on_delete=models.PROTECT, related_name='ledgers', blank=True, null=True,)
    opening_balance = models.FloatField(default=0.00, blank=True, null=True)
    types = models.CharField(max_length=2, choices=DR_CR_CHOICES, blank=True, null=True)
    remark = models.TextField(blank=True, null=True)
    trn_number = models.CharField(max_length=50, blank=True, null=True)
    cr_no = models.CharField(max_length=50, blank=True, null=True)

    email = models.EmailField(blank=True, null=True)
    mobile = models.CharField(max_length=15, blank=True, null=True)
    phone_no = models.CharField(max_length=15, blank=True, null=True)
    address1 = models.TextField(blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    zipcode = models.CharField(max_length=10, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    isDefault = models.BooleanField(default=False)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    
    created_by = models.IntegerField(null=True, blank=True)   
    updated_by = models.IntegerField(null=True, blank=True)
    
    
    
    

    def __str__(self):
       return f"{self.ledger_name}"





    
class LocalPayment(models.Model):
    PAYMENT_MODES = [
        ('cash', 'Cash'),
        ('bank', 'Bank'),
        ('cheque', 'Cheque')
    ]

    date = models.DateField( default=timezone.now)
    voucher_no = models.CharField(max_length=20, unique=True)
    voucherType = models.ForeignKey('fleet_app.Vouchers', on_delete=models.PROTECT, default=11)
    payment_mode = models.ForeignKey(LedgerCreation, on_delete=models.PROTECT, related_name="local_payment_master_ledger")
    party = models.CharField(max_length=100)
    reference_no = models.CharField(max_length=50, blank=True, null=True)
    party_VAT_no = models.CharField(max_length=20, blank=True, null=True)
    IsPDC = models.BooleanField(default=False)
    Cleared = models.CharField(max_length=100)
    BounceCharge = models.DecimalField(max_digits=15, decimal_places=3, default=0)
    ChequeDate = models.DateField(null=True, blank=True)
    ChequeNo = models.CharField(max_length=100, null=True, blank=True)
    remark = models.TextField(blank=True, null=True)
    note = models.TextField(blank=True, null=True)
    taxable_amount = models.DecimalField(max_digits=15, decimal_places=3)
    VAT_amount = models.DecimalField(max_digits=15, decimal_places=3)
    net_amount = models.DecimalField(max_digits=15, decimal_places=3)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Local Payment - {self.voucher_no}"

class LocalPaymentItems(models.Model):
    VAT_TYPES = [
        (1, 'No VAT'),
        (2, 'Inclusive VAT (5%)'),
        (3, 'Exclusive VAT (5%)')
    ]
    localpayment = models.ForeignKey(LocalPayment, on_delete=models.PROTECT, related_name='items')
    invoice_date = models.DateField(default=timezone.now)
    invoice_no = models.CharField(max_length=50)
    ledger = models.ForeignKey('LedgerCreation', on_delete=models.PROTECT)
    description = models.CharField(blank=True, null=True, max_length=255)
    amount = models.DecimalField(max_digits=15, decimal_places=3)
    vat_type = models.IntegerField(choices=VAT_TYPES, default=1)
    vat_amount = models.DecimalField(max_digits=15, decimal_places=3, default=0) 
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)


    def __str__(self):
        return f"Item for {self.localpayment.voucher_no} - Invoice {self.invoice_no}"

class LocalPaymentCheque(models.Model):
    CHEQUE_STATUS = [
        ('holding', 'Holding'),
        ('collected', 'Collected'),
        ('bounced', 'Bounced')
    ]

    localpayment = models.ForeignKey(LocalPayment, on_delete=models.PROTECT, related_name='cheques')
    cheque_no = models.CharField(max_length=50, blank=True, null=True)
    cheque_date = models.DateField(blank=True, null=True)
    issuing_bank_name = models.CharField(max_length=100, blank=True, null=True)
    reference_no = models.CharField(max_length=50, blank=True, null=True)
    cheque_status = models.CharField(max_length=10, choices=CHEQUE_STATUS, blank=True, null=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cheque {self.cheque_no} - Status {self.cheque_status}"    
    
class Payment(models.Model):
    PAYMENT_MODE_CHOICES = [
        ("cash", "Cash"),
        ("bank", "Bank"),
    ]

    PAYMENT_TYPE_CHOICES = [
        ("cheque", "Cheque"),
        ("transfer", "Bank Transfer"),
        ("upi", "UPI"),
    ]

    # Basic voucher and tracking fields
    voucher_no = models.CharField(max_length=50, blank=True, null=True)
    PaymentNo = models.CharField(max_length=50, unique=True)
    Date = models.DateField( default=timezone.now)
    voucherType = models.ForeignKey('fleet_app.Vouchers', on_delete=models.PROTECT, default=3, related_name="payment_voucher_type")

    # Ledger information
    LedgerCr = models.ForeignKey( LedgerCreation,on_delete=models.PROTECT,related_name="payment_credit_entries")
    LedgerDr = models.ForeignKey(LedgerCreation,on_delete=models.PROTECT,related_name="payment_debit_entries")

    # Payment details
    PaymentMode = models.CharField(max_length=10, choices=PAYMENT_MODE_CHOICES, default="cash")
    PaymentType = models.CharField(max_length=10, choices=PAYMENT_TYPE_CHOICES, blank=True, null=True)
    BankTransferID = models.CharField(max_length=100, blank=True, null=True)

    # Cheque and clearance details
    IsPDC = models.BooleanField(default=False, help_text="Is Post Dated Cheque?")
    Cleared = models.BooleanField(default=False)
    ChequeDate = models.DateField(blank=True, null=True)
    ChequeNo = models.CharField(max_length=50, blank=True, null=True)

    # Reference to source voucher (Hire)
    RefVoucherType = models.ForeignKey('fleet_app.Vouchers',on_delete=models.SET_NULL,null=True,blank=True,related_name="payments_ref_voucher_type",)
    RefVoucherNo = models.PositiveIntegerField(blank=True, null=True)

    # Optional remarks / metadata
    Remarks = models.TextField(blank=True, null=True)
    
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    created_by = models.IntegerField(null=True, blank=True)   
    updated_by = models.IntegerField(null=True, blank=True) 
    
    def save(self, *args, **kwargs):
        if not self.voucher_no and self.voucherType:
            self.voucher_no = self.voucherType.get_next_voucher_number()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Payment #{self.PaymentNo} - {self.LedgerDr} → {self.LedgerCr}"
        
class Receipt(models.Model):
    
    PAYMENT_MODE_CHOICES = [
        ('cash', 'Cash'),
        ('bank', 'Bank'),
        ('cheque', 'Cheque'),
    ]

    VOUCHER_TYPE_CHOICES = [
        ('Cr', 'Cr'),
        ('Dr', 'Dr'),
    ]

    voucher_no = models.CharField(max_length=20, unique=True)
    date = models.DateField()
    payment_type = models.CharField(max_length=10, choices=VOUCHER_TYPE_CHOICES, default='Dr')
    payment_mode = models.CharField(max_length=10, choices=PAYMENT_MODE_CHOICES, default='Cash')
    reference_no = models.CharField(max_length=50, blank=True, null=True)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=3, default=0.00, null=True, blank=True)
    taxable_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    VAT_amount = models.DecimalField(max_digits=10, decimal_places=3, default=0.00)
    net_amount = models.DecimalField(max_digits=10, decimal_places=3, default=0.00)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.voucher_no} - {self.customer}"


class ReceiptItems(models.Model):
    receipt = models.ForeignKey(Receipt, on_delete=models.PROTECT, related_name='items')
    ledger = models.ForeignKey('LedgerCreation', on_delete=models.PROTECT, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=3, default=0.00, blank=True, null=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.receipt.voucher_no} - {self.ledger}"  
    
class ReceiptCheque(models.Model):
    CHEQUE_STATUS = [
        ('holding', 'Holding'),
        ('collected', 'Collected'),
        ('bounced', 'Bounced')
    ]

    receipt = models.ForeignKey(Receipt, on_delete=models.PROTECT, related_name='cheques')
    cheque_no = models.CharField(max_length=50, blank=True, null=True)
    cheque_date = models.DateField(blank=True, null=True)
    issuing_bank_name = models.CharField(max_length=100, blank=True, null=True)
    reference_no = models.CharField(max_length=50, blank=True, null=True)
    cheque_status = models.CharField(max_length=10, choices=CHEQUE_STATUS, blank=True, null=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cheque {self.cheque_no} - Status {self.cheque_status}"      
     
class Contra(models.Model):
    CONTRA_TYPE_CHOICES = [
        ('Deposit', 'Deposit'),
        ('Withdrawal', 'Withdrawal'),
        ('Transfer', 'Transfer'),
    ]

    date = models.DateField()
    voucher_no = models.CharField(max_length=20, unique=True)
    contra_type = models.CharField(max_length=10, choices=CONTRA_TYPE_CHOICES)
    dr_ledger = models.ForeignKey('LedgerCreation', on_delete=models.PROTECT, related_name='contra_dr_ledger')
    cr_ledger = models.ForeignKey('LedgerCreation', on_delete=models.PROTECT, related_name='contra_cr_ledger')
    cheque_no = models.CharField(max_length=20, null=True, blank=True)
    cheque_date = models.DateField(null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=3)
    remark = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"Contra {self.voucher_no} - {self.contra_type}"

    class Meta:
        ordering = ['-date']
        
class Journal(models.Model):
    date = models.DateField()
    voucher_no = models.CharField(max_length=20, unique=True)
    dr_ledger = models.ForeignKey(LedgerCreation, related_name='dr_journals', on_delete=models.PROTECT)
    cr_ledger = models.ForeignKey(LedgerCreation, related_name='cr_journals', on_delete=models.PROTECT)
    due_date = models.DateField()
    amount = models.DecimalField(max_digits=10, decimal_places=3)
    narration = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.voucher_no} - {self.date}"

        
        
class LedgerPosting(models.Model):
    date = models.DateField()
    VoucherType = models.ForeignKey('fleet_app.Vouchers', on_delete=models.PROTECT, related_name='FleetVoucherType')
    VoucherNo = models.BigIntegerField() #id of all vouchers
    ledger = models.ForeignKey(LedgerCreation, on_delete=models.PROTECT)
    debit = models.DecimalField(max_digits=10, decimal_places=3, blank=True, null=True)
    credit = models.DecimalField(max_digits=10, decimal_places=3, blank=True, null=True)
    RefVoucherNo = models.BigIntegerField(null=True, blank=True)
    RefVoucherType = models.ForeignKey('fleet_app.Vouchers', on_delete=models.PROTECT, null=True, blank=True, related_name='RefVoucherType')
    CostCenter = models.ForeignKey('item_master.CostCenter', on_delete=models.PROTECT, blank=True, null=True) # not need now
    FY = models.IntegerField(null=True, blank=True) # will change to Fk in future
    IsDeleted = models.BooleanField(default=False)
    
    
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    created_by = models.IntegerField(null=True, blank=True)   
    updated_by = models.IntegerField(null=True, blank=True)          
    
class BillClearance(models.Model):
    PAYMENT_MODE_CHOICES = [
        ('cash', 'Cash'),
        ('bank', 'Bank'),
    ]

    CHEQUE_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('cleared', 'Cleared'),
        ('bounced', 'Bounced'),
        ('cancelled', 'Cancelled'),
    ]

    # Core fields
    Ledger = models.ForeignKey(LedgerCreation, on_delete=models.PROTECT, related_name="bill_clearances_main")
    RefVoucherNo = models.PositiveIntegerField()
    RefVoucherType = models.ForeignKey('fleet_app.Vouchers', on_delete=models.PROTECT, related_name="bill_clearances")
    InvAmount = models.DecimalField(max_digits=15, decimal_places=3, default=0)
    Balance = models.DecimalField(max_digits=15, decimal_places=3, default=0)
    Amount = models.DecimalField(max_digits=15, decimal_places=3, default=0)
    Date = models.DateField()
    PaymentMode = models.CharField(max_length=10, choices=PAYMENT_MODE_CHOICES, null=True, blank=True)

    # For double ledger entry (e.g. bank)
    Ledger2 = models.ForeignKey(LedgerCreation, on_delete=models.SET_NULL, null=True, blank=True, related_name="bill_clearances_counter")
    TrnNo = models.PositiveIntegerField(null=True, blank=True)
    # Optional cheque details (used only if PaymentMode = 'bank')
    ChequeNo = models.CharField(max_length=50, blank=True, null=True)
    ChequeDate = models.DateField(blank=True, null=True)
    ChequeStatus = models.CharField(max_length=10, choices=CHEQUE_STATUS_CHOICES, blank=True, null=True)
    
    Type = models.ForeignKey('fleet_app.Vouchers', on_delete=models.PROTECT, related_name="Payment_Receipt")
    
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    created_by = models.IntegerField(null=True, blank=True)   
    updated_by = models.IntegerField(null=True, blank=True) 

    def __str__(self):
        return f"BillClearance #{self.id} - {self.RefVoucherType} #{self.RefVoucherNo}"


class ReceiptBillMaster(models.Model):    
    CHEQUE_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('cleared', 'Cleared'),
        ('bounced', 'Bounced'),
        ('cancelled', 'Cancelled'),
    ]
    Date = models.DateField( default=timezone.now )
    Customer = models.ForeignKey(LedgerCreation, on_delete=models.PROTECT, related_name='receipt_party', blank=True, null=True)
    Ledger = models.ForeignKey(LedgerCreation, on_delete=models.PROTECT, related_name='cash_bank')
    TotalAmount = models.DecimalField(max_digits=15, decimal_places=3, default=0)
    Remark = models.TextField(null=True, blank=True)
    TrnNo = models.PositiveIntegerField(null=True, blank=True)
    IsPDC = models.BooleanField(default=False)
    Cleared = models.CharField(max_length=100)
    BounceCharge = models.DecimalField(max_digits=15, decimal_places=3, default=0)
    ChequeNo = models.CharField(max_length=50, blank=True, null=True)
    ChequeDate = models.DateField(blank=True, null=True)
    ChequeStatus = models.CharField(max_length=10, choices=CHEQUE_STATUS_CHOICES, blank=True, null=True)
    
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    created_by = models.IntegerField(null=True, blank=True)   
    updated_by = models.IntegerField(null=True, blank=True)

class ReceiptBillDetails(models.Model):
    BillMaster = models.ForeignKey(ReceiptBillMaster, on_delete=models.CASCADE)
    voucherType = models.ForeignKey('fleet_app.Vouchers', on_delete=models.PROTECT, related_name='receiptbill_voucher_type', default=5)
    VoucherNo = models.PositiveIntegerField()
    CurrentAmount = models.DecimalField(max_digits=15, decimal_places=3, default=0)
    Amount = models.DecimalField(max_digits=15, decimal_places=3, default=0)
    
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    created_by = models.IntegerField(null=True, blank=True)
    updated_by = models.IntegerField(null=True, blank=True)    
    
class PaymentBillMaster(models.Model):    
    CHEQUE_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('cleared', 'Cleared'),
        ('bounced', 'Bounced'),
        ('cancelled', 'Cancelled'),
    ]
    Date = models.DateField( default=timezone.now )
    Supplier = models.ForeignKey(LedgerCreation, on_delete=models.PROTECT, related_name='Payment_party', blank=True, null=True)
    Ledger = models.ForeignKey(LedgerCreation, on_delete=models.PROTECT, related_name='Payment_cash_bank')
    TotalAmount = models.DecimalField(max_digits=15, decimal_places=3, default=0)
    Remark = models.TextField(null=True, blank=True)
    TrnNo = models.PositiveIntegerField(null=True, blank=True)
    IsPDC = models.BooleanField(default=False)
    Cleared = models.CharField(max_length=100)
    BounceCharge = models.DecimalField(max_digits=15, decimal_places=3, default=0)
    ChequeNo = models.CharField(max_length=50, blank=True, null=True)
    ChequeDate = models.DateField(blank=True, null=True)
    ChequeStatus = models.CharField(max_length=10, choices=CHEQUE_STATUS_CHOICES, blank=True, null=True)
    
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    created_by = models.IntegerField(null=True, blank=True)   
    updated_by = models.IntegerField(null=True, blank=True)

class PaymentBillDetails(models.Model):
    BillMaster = models.ForeignKey(PaymentBillMaster, on_delete=models.CASCADE)
    voucherType = models.ForeignKey('fleet_app.Vouchers', on_delete=models.PROTECT, related_name='paymentbill_voucher_type', default=6)
    VoucherNo = models.PositiveIntegerField()
    CurrentAmount = models.DecimalField(max_digits=15, decimal_places=3, default=0)
    Amount = models.DecimalField(max_digits=15, decimal_places=3, default=0)
    
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    created_by = models.IntegerField(null=True, blank=True)
    updated_by = models.IntegerField(null=True, blank=True)        
    

class PaymentMaster(models.Model):
    voucher_no = models.CharField(max_length=100)
    voucherType = models.ForeignKey('fleet_app.Vouchers', on_delete=models.PROTECT, default=3, related_name="payment_master_voucher_type")
    Date = models.DateField( default=timezone.now )
    Ledger = models.ForeignKey(LedgerCreation, on_delete=models.PROTECT, related_name="payment_master_ledger")
    PaidTo = models.CharField(max_length=255)
    IsPDC = models.BooleanField(default=False)
    Cleared = models.CharField(max_length=100)
    BounceCharge = models.DecimalField(max_digits=15, decimal_places=3, default=0)
    ChequeDate = models.DateField(null=True, blank=True)
    ChequeNo = models.CharField(max_length=100, null=True, blank=True)
    TotalAmount = models.DecimalField(max_digits=15, decimal_places=3, default=0)
    FyId = models.IntegerField( null=True, blank=True)
    
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    created_by = models.IntegerField(null=True, blank=True)
    updated_by = models.IntegerField(null=True, blank=True)     

    def __str__(self):
        return f"Voucher {self.voucher_no}"


class PaymentDetails(models.Model):
    Payment = models.ForeignKey(PaymentMaster, on_delete=models.CASCADE, related_name="details")
    Ledger = models.ForeignKey(LedgerCreation, on_delete=models.PROTECT, related_name="payment_detail_ledger")
    Amount = models.DecimalField(max_digits=12, decimal_places=3)
    Desc = models.TextField(null=True, blank=True)
    Vehicle = models.ForeignKey('fleet_app.Vehicle', on_delete=models.SET_NULL, null=True, blank=True, related_name="payment_details")
    FyId = models.IntegerField( null=True, blank=True)
    
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    created_by = models.IntegerField(null=True, blank=True)
    updated_by = models.IntegerField(null=True, blank=True)     

    def __str__(self):
        return f"Detail for Voucher {self.Payment.voucher_no}"    
    
class ReceiptMaster(models.Model):
    voucher_no = models.CharField(max_length=100)
    voucherType = models.ForeignKey('fleet_app.Vouchers', on_delete=models.PROTECT, default=4, related_name="receipt_master_voucher_type")
    Date = models.DateField( default=timezone.now )
    Ledger = models.ForeignKey(LedgerCreation, on_delete=models.PROTECT, related_name="receipt_master_ledger")
    ReceivedFrom = models.CharField(max_length=255)
    IsPDC = models.BooleanField(default=False)
    Cleared = models.CharField(max_length=100)
    BounceCharge = models.DecimalField(max_digits=15, decimal_places=3, default=0)
    ChequeDate = models.DateField(null=True, blank=True)
    ChequeNo = models.CharField(max_length=100, null=True, blank=True)
    TotalAmount = models.DecimalField(max_digits=15, decimal_places=3, default=0)
    FyId = models.IntegerField( null=True, blank=True)
    
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    created_by = models.IntegerField(null=True, blank=True)
    updated_by = models.IntegerField(null=True, blank=True)     

    def __str__(self):
        return f"Voucher {self.voucher_no}"


class ReceiptDetails(models.Model):
    Receipt = models.ForeignKey(ReceiptMaster, on_delete=models.CASCADE, related_name="details")
    Ledger = models.ForeignKey(LedgerCreation, on_delete=models.PROTECT, related_name="receipt_detail_ledger")
    Amount = models.DecimalField(max_digits=12, decimal_places=3)
    Desc = models.TextField(null=True, blank=True)
    FyId = models.IntegerField( null=True, blank=True)
    
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    created_by = models.IntegerField(null=True, blank=True)
    updated_by = models.IntegerField(null=True, blank=True)     

    def __str__(self):
        return f"Detail for Voucher {self.Receipt.voucher_no}"
    
class BillWiseOpening(models.Model):
    DR_CR_CHOICES = (('DR', 'Dr'), ('CR', 'Cr'))
    ledger = models.ForeignKey('accounts_app.LedgerCreation', on_delete=models.PROTECT, related_name='billwise_openings')
    voucherType = models.ForeignKey('fleet_app.Vouchers', on_delete=models.PROTECT)
    InvNo = models.CharField(max_length=100)
    InvDate = models.DateField(default=timezone.now)
    InvAmount = models.DecimalField(max_digits=12, decimal_places=3)
    InvBalance = models.DecimalField(max_digits=12, decimal_places=3)
    dr_cr = models.CharField(max_length=2, choices=DR_CR_CHOICES)
    IsCleared = models.BooleanField(default=False)
    IsClosed = models.BooleanField(default=False)
    CreatedOn = models.DateTimeField(auto_now_add=True)
    UpdatedOn = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['InvDate']
        unique_together = ('ledger', 'InvNo', 'voucherType')

    def __str__(self):
        return f"{self.ledger.ledger_name} - {self.InvNo}"    