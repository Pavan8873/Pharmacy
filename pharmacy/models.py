from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('employee', 'Employee'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)

    def __str__(self):
        return f"{self.user.username} - {self.role}"

class Company(models.Model):
    name = models.CharField(max_length=255)
    license_no = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    contact_no = models.CharField(max_length=255)
    email = models.EmailField()
    description = models.TextField()
    added_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Medicine(models.Model):
    name = models.CharField(max_length=255)
    medical_type = models.CharField(max_length=255)
    buy_price = models.DecimalField(max_digits=10, decimal_places=2)
    sell_price = models.DecimalField(max_digits=10, decimal_places=2)
    c_gst = models.DecimalField(max_digits=5, decimal_places=2)
    s_gst = models.DecimalField(max_digits=5, decimal_places=2)
    batch_no = models.CharField(max_length=255)
    shelf_no = models.CharField(max_length=255)
    expire_date = models.DateField()
    mfg_date = models.DateField()
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    description = models.TextField()
    in_stock_total = models.IntegerField()
    qty_in_strip = models.IntegerField()
    added_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Customer(models.Model):
    name = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    contact = models.CharField(max_length=255)
    added_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

from django.db import models

class Bill(models.Model):
    customer = models.ForeignKey('Customer', on_delete=models.CASCADE)
    added_on = models.DateTimeField(auto_now_add=True)

    def total_amount(self):
        # Calculate the total amount for the entire bill
        return sum(detail.amount() for detail in self.billdetails_set.all())

    def total_profit(self):
        # Calculate the total profit for the entire bill
        return sum(detail.profit() for detail in self.billdetails_set.all())

class BillDetails(models.Model):
    bill = models.ForeignKey(Bill, on_delete=models.CASCADE)
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE)
    qty = models.IntegerField()
    added_on = models.DateTimeField(auto_now_add=True)

    def amount(self):
        # Calculate total amount for this item (quantity * sell price)
        return self.medicine.sell_price * self.qty

    def profit(self):
        # Calculate profit for this item (quantity * (sell price - buy price))
        return (self.medicine.sell_price - self.medicine.buy_price) * self.qty


from django.db import models

class PurchaseBill(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)  # Linking to the Company
    bill_number = models.CharField(max_length=20, unique=True)  # Unique Bill Number
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # Total amount
    added_on = models.DateTimeField(auto_now_add=True)  # Timestamp of when the bill was created

    def __str__(self):
        return f"Purchase Bill {self.bill_number} from {self.company.name}"

    def calculate_total_amount(self):
        """Calculates total amount for the purchase bill."""
        total = sum(item.medicine.buy_price * item.qty for item in self.purchasebilldetails_set.all())
        self.total_amount = total
        self.save()


class PurchaseBillDetails(models.Model):
    purchase_bill = models.ForeignKey(PurchaseBill, on_delete=models.CASCADE)  # Link to the purchase bill
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE)  # Linking to the Medicine
    qty = models.IntegerField()  # Quantity purchased
    medicine_price = models.DecimalField(max_digits=10, decimal_places=2)  # Price at which the shop buys the medicine
    added_on = models.DateTimeField(auto_now_add=True)  # Timestamp of when the medicine was added to the bill

    def __str__(self):
        return f"{self.medicine.name} x {self.qty} at {self.medicine_price} each"
# from django.db import models
# from datetime import date

# class PurchaseHistory(models.Model):
#     MEDICINE_TYPES = [
#         ('tablet', 'Tablet'),
#         ('cream/jel', 'Cream/Jel'),
#         ('liquid', 'Liquid'),
#     ]

#     medicine_name = models.CharField(max_length=255)
#     medicine_type = models.CharField(max_length=50, choices=MEDICINE_TYPES)
#     Number_of_medicines_per_strip = models.PositiveIntegerField(help_text="Number of packs (e.g., 6s or 10s)")
#     qty_in_strip = models.PositiveIntegerField()
#     free_medicine_qty = models.PositiveIntegerField(default=0)
#     company_name = models.CharField(max_length=255)
#     expiry_date = models.DateField()
#     mrp_rate = models.DecimalField(max_digits=10, decimal_places=2, help_text="Selling price")
#     shop_rate = models.DecimalField(max_digits=10, decimal_places=2, help_text="Buying price")
#     total_amount = models.DecimalField(max_digits=10, decimal_places=2)
#     purchase_date = models.DateField(auto_now_add=True)
    

#     def __str__(self):
#         return f"{self.medicine_name} from {self.company_name}"

#     @property
#     def is_expired(self):
#         return self.expiry_date < date.today()
# from django.db import models
# from datetime import date

# class Bill1(models.Model):  # Renamed Bill1 to Bill
#     PAYMENT_STATUS = [
#         ('paid', 'Paid'),
#         ('pending', 'Pending'),
#     ]

#     PAYMENT_MODE = [
#         ('cash', 'Cash'),
#         ('cheque', 'Cheque'),
#     ]

#     bill_number = models.CharField(max_length=100, unique=True)
#     bill_date = models.DateField()
#     bill_amount = models.DecimalField(max_digits=10, decimal_places=2)
#     payment_status = models.CharField(max_length=10, choices=PAYMENT_STATUS)
#     payment_mode = models.CharField(max_length=10, choices=PAYMENT_MODE)
#     cheque_number = models.CharField(max_length=100, null=True, blank=True)  # Optional, for cheque payments
#     cheque_date = models.DateField(null=True, blank=True)  # Optional, for cheque payments

#     def __str__(self):
#         return f"Bill #{self.bill_number} - {self.payment_status.title()} ({self.payment_mode.title()})"


# class PurchaseHistory(models.Model):
#     MEDICINE_TYPES = [
#         ('tablet', 'Tablet'),
#         ('capsule', 'Capsule'),
#         ('sachet', 'Sachet'),
#         ('cream', 'Cream'),
#         ('fluid', 'Fluid'),
#         ('injection', 'Injection'),
#     ]
#     UNIT_TYPE = [
#         ('strip', 'Strip-wise'),
#         ('unit', 'Unit-wise'),
#     ]
#     bill = models.ForeignKey('Bill1', on_delete=models.CASCADE, related_name='purchases', null=True, blank=True)
#     batch_number = models.CharField(max_length=100, null=True, blank=True)
#     medicine_name = models.CharField(max_length=255)
#     medicine_type = models.CharField(max_length=50, choices=MEDICINE_TYPES)
#     # Automatic based on medicine type
#     unit_type = models.CharField(
#         max_length=10,
#         choices=[('strip', 'Strip-wise'), ('unit', 'Unit-wise')],
#         null=True,
#         blank=True,
#     )
#     Number_of_medicines_per_strip = models.PositiveIntegerField(
#         help_text="Applicable for strip-wise medicines only", null=True, blank=True
#     )
#     qty_in_strip = models.PositiveIntegerField()
#     free_medicine_qty = models.PositiveIntegerField(default=0)
#     company_name = models.CharField(max_length=255)
#     expiry_date = models.DateField()
#     mrp_rate = models.DecimalField(max_digits=10, decimal_places=2, help_text="Selling price")
#     shop_rate = models.DecimalField(max_digits=10, decimal_places=2, help_text="Buying price")
#     total_amount = models.DecimalField(max_digits=10, decimal_places=2)
#     purchase_date = models.DateField(auto_now_add=True)

#     def __str__(self):
#         return f"{self.medicine_name} from {self.company_name} (Batch {self.batch_number})"

#     @property
#     def is_expired(self):
#         return self.expiry_date < date.today()

#     def save(self, *args, **kwargs):
#         # Automatically set unit type based on medicine_type
#         if self.medicine_type in ['tablet', 'capsule']:
#             self.unit_type = 'strip'
#         else:
#             self.unit_type = 'unit'
#         super().save(*args, **kwargs)
class Bill1(models.Model):  # Renamed from Bill1
    PAYMENT_STATUS = [
        ('paid', 'Paid'),
        ('pending', 'Pending'),
    ]

    PAYMENT_MODE = [
        ('cash', 'Cash'),
        ('cheque', 'Cheque'),
    ]

    bill_number = models.CharField(max_length=100, unique=True)
    bill_date = models.DateField(null=True, blank=True)


    bill_amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_status = models.CharField(max_length=10, choices=PAYMENT_STATUS)
    payment_mode = models.CharField(max_length=10, choices=PAYMENT_MODE)
    cheque_number = models.CharField(max_length=100, null=True, blank=True)
    cheque_date = models.DateField(null=True, blank=True)
    combined_pay = models.CharField(max_length=100, null=True, blank=True)


    def __str__(self):
        return f"Bill #{self.bill_number} - {self.payment_status.title()} ({self.payment_mode.title()})"


# class PurchaseHistory(models.Model):
#     MEDICINE_TYPES = [
#         ('tablet', 'Tablet'),
#         ('capsule', 'Capsule'),
#         ('sachet', 'Sachet'),
#         ('cream', 'Cream'),
#         ('fluid', 'Fluid'),
#         ('injection', 'Injection'),
#     ]

#     bill = models.ForeignKey(Bill1, on_delete=models.CASCADE, related_name='purchases')  # fixed FK
#     batch_number = models.CharField(max_length=100, null=True, blank=True)
#     medicine_name = models.CharField(max_length=255)
#     medicine_type = models.CharField(max_length=50, choices=MEDICINE_TYPES)
#     unit_type = models.CharField(max_length=10, choices=[('strip', 'Strip-wise'), ('unit', 'Unit-wise')], null=True, blank=True)
#     Number_of_medicines_per_strip = models.PositiveIntegerField(null=True, blank=True)
#     qty_in_strip = models.PositiveIntegerField()
#     free_medicine_qty = models.PositiveIntegerField(default=0)
#     company_name = models.CharField(max_length=255)
#     expiry_date = models.DateField()
#     mrp_rate = models.DecimalField(max_digits=10, decimal_places=2)
#     shop_rate = models.DecimalField(max_digits=10, decimal_places=2)
#     total_amount = models.DecimalField(max_digits=10, decimal_places=2)
#     purchase_date = models.DateField(auto_now_add=True)
#     discount = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, help_text="Discount percentage")

#     def __str__(self):
#         return f"{self.medicine_name} from {self.company_name} (Batch {self.batch_number})"

#     @property
#     def is_expired(self):
#         return self.expiry_date < date.today()

#     def save(self, *args, **kwargs):
#         if self.medicine_type in ['tablet', 'capsule']:
#             self.unit_type = 'strip'
#         else:
#             self.unit_type = 'unit'
#         super().save(*args, **kwargs)

from django.db import models
from datetime import date

class PurchaseHistory(models.Model):
    bill = models.ForeignKey(Bill1, on_delete=models.CASCADE, related_name='purchases')  # fixed FK
    batch_number = models.CharField(max_length=100, null=True, blank=True)
    medicine_name = models.CharField(max_length=255)
    qty_in_strip = models.DecimalField(max_digits=5, decimal_places=1)
    free_medicine_qty = models.PositiveIntegerField(default=0)
    company_name = models.CharField(max_length=255)
    expiry_date = models.DateField()
    mrp_rate = models.DecimalField(max_digits=10, decimal_places=2)
    shop_rate = models.DecimalField(max_digits=10, decimal_places=2)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    purchase_date = models.DateField(auto_now_add=True)
    qty_in_strip_history = models.IntegerField()
    free_medicine_qty_history = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.medicine_name} from {self.company_name} (Batch {self.batch_number})"

    @property
    def is_expired(self):
        return self.expiry_date < date.today()

class SalesRegister(models.Model):
    customer_name = models.CharField(max_length=255)
    bill_number = models.CharField(max_length=100)
    medicine = models.ForeignKey(PurchaseHistory, on_delete=models.CASCADE)
    qty_in_strips = models.PositiveIntegerField(default=0)
    qty_in_loose = models.PositiveIntegerField(default=0)
    discount = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    sale_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Sale to {self.customer_name} - {self.medicine.medicine_name}"
from django.db import models

class MedicineMaster(models.Model):
    MEDICINE_TYPES = [
        ('tablet', 'Tablet'),
        ('capsule', 'Capsule'),
        ('sachet', 'Sachet'),
        ('cream/jel', 'Cream/Jel'),
        ('liquid', 'Liquid'),
        ('cream', 'Cream'),
        ('fluid', 'Fluid'),
        ('injection', 'Injection'),
    ]

    medicine_name = models.CharField(max_length=255)
    medicine_type = models.CharField(max_length=50, choices=MEDICINE_TYPES)
    Number_of_medicines_per_strip = models.PositiveIntegerField(help_text="Number of packs (e.g., 6s or 10s)")
    purchase_date = models.DateField(auto_now_add=True)
    discount = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, help_text="Discount percentage")

    def __str__(self):
        return f"{self.medicine_name} "

# models.py

from django.db import models

class Vendor(models.Model):
    
    name = models.CharField(max_length=100)
    address = models.TextField()
    telephone = models.CharField(max_length=15)
    gstin = models.CharField(max_length=15)

    def __str__(self):
        return self.name
