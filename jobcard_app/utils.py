import re

def get_voucher_master(voucher_type_name):
    """
    Lookup Voucher Master record from fleet_app.models.Vouchers.
    Flexible matching by exact VoucherType, VoucherName, or case/space-insensitive match.
    """
    from fleet_app.models import Vouchers
    v = Vouchers.objects.filter(VoucherType__iexact=voucher_type_name).first()
    if not v:
        v = Vouchers.objects.filter(VoucherName__iexact=voucher_type_name).first()
    if not v:
        clean_name = voucher_type_name.replace(' ', '').lower()
        for voucher in Vouchers.objects.all():
            v_type_clean = (voucher.VoucherType or '').replace(' ', '').lower()
            v_name_clean = (voucher.VoucherName or '').replace(' ', '').lower()
            if v_type_clean == clean_name or v_name_clean == clean_name:
                return voucher
    return v


def generate_voucher_number(voucher_type_name, model_cls, number_field_name, default_prefix=""):
    """
    Common reusable document/voucher number generator.
    Reads Prefix, Suffix, MinLength, and StartingNo from Voucher Master (fleet_app.models.Vouchers).
    Calculates next sequence number based on existing database records for model_cls,
    and guarantees duplicate-free voucher numbers.
    """
    voucher = get_voucher_master(voucher_type_name)

    prefix = (voucher.Prefix if (voucher and voucher.Prefix is not None) else default_prefix) or ""
    suffix = (voucher.Suffix if (voucher and voucher.Suffix is not None) else "") or ""
    min_length = voucher.MinLength if (voucher and voucher.MinLength) else 5
    starting_no = voucher.StartingNo if (voucher and voucher.StartingNo) else 1

    # Query all existing values for number_field_name in model_cls
    existing_records = model_cls.objects.exclude(
        **{f"{number_field_name}__isnull": True}
    ).exclude(
        **{number_field_name: ""}
    ).values_list(number_field_name, flat=True)

    max_num = starting_no - 1

    for val in existing_records:
        val_str = str(val).strip()
        if not val_str:
            continue

        temp_str = val_str
        matched_prefix = False

        # If prefix is set, only parse records matching the prefix
        if prefix:
            if temp_str.startswith(prefix):
                temp_str = temp_str[len(prefix):]
                matched_prefix = True
            else:
                prefix_nohyphen = prefix.rstrip('-')
                if temp_str.startswith(prefix_nohyphen):
                    temp_str = temp_str[len(prefix_nohyphen):]
                    if temp_str.startswith('-'):
                        temp_str = temp_str[1:]
                    matched_prefix = True
        else:
            matched_prefix = True

        if not matched_prefix:
            continue

        # Remove suffix if present
        if suffix and temp_str.endswith(suffix):
            temp_str = temp_str[:-len(suffix)]

        # Extract numeric digits
        digits = ''.join(filter(str.isdigit, temp_str))
        if digits:
            try:
                num = int(digits)
                max_num = max(max_num, num)
            except ValueError:
                pass

    next_num = max(max_num + 1, starting_no)

    # Enforce uniqueness loop to prevent duplicate voucher numbers
    while True:
        formatted_seq = str(next_num).zfill(min_length)
        candidate = f"{prefix}{formatted_seq}{suffix}"
        if not model_cls.objects.filter(**{number_field_name: candidate}).exists():
            return candidate
        next_num += 1
