from django import forms
from django.contrib.auth.models import User
from .models import Profile, Company, Medicine, Customer
class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter your password'}))
    role = forms.ChoiceField(choices=Profile.ROLE_CHOICES, widget=forms.Select(attrs={'class': 'form-select'}))

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'role']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your username'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter your email address'}),
        }

from django import forms
from .models import Company

class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = '__all__'
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter company name'}),
            'license_no': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter license number'}),
            'address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter address'}),
            'contact_no': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter contact number'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter email'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter description'}),
        }


class MedicineForm(forms.ModelForm):
    class Meta:
        model = Medicine
        fields = '__all__'
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'medical_type': forms.TextInput(attrs={'class': 'form-control'}),
            'buy_price': forms.NumberInput(attrs={'class': 'form-control'}),
            'sell_price': forms.NumberInput(attrs={'class': 'form-control'}),
            'c_gst': forms.NumberInput(attrs={'class': 'form-control'}),
            's_gst': forms.NumberInput(attrs={'class': 'form-control'}),
            'batch_no': forms.TextInput(attrs={'class': 'form-control'}),
            'shelf_no': forms.TextInput(attrs={'class': 'form-control'}),
            'expire_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'mfg_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'company': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'in_stock_total': forms.NumberInput(attrs={'class': 'form-control'}),
            'qty_in_strip': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = '__all__'
from django import forms
from .models import PurchaseHistory

class PurchaseHistoryForm(forms.ModelForm):
    class Meta:
        model = PurchaseHistory
        fields = [
            'medicine_name',
            'qty_in_strip',
            'free_medicine_qty',
            'company_name',
            'expiry_date',
            'mrp_rate',
            'shop_rate'
        ]
        widgets = {
            'medicine_name': forms.TextInput(attrs={'class': 'form-control'}),
            'qty_in_strip': forms.NumberInput(attrs={'class': 'form-control'}),
            'free_medicine_qty': forms.NumberInput(attrs={'class': 'form-control'}),
            'company_name': forms.TextInput(attrs={'class': 'form-control'}),
            'expiry_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'mrp_rate': forms.NumberInput(attrs={'class': 'form-control'}),
            'shop_rate': forms.NumberInput(attrs={'class': 'form-control'}),
        }

# forms.py

from django import forms
from .models import Vendor

class VendorForm(forms.ModelForm):
    class Meta:
        model = Vendor
        fields = ['name', 'address', 'telephone', 'gstin']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'address': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'telephone': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'gstin': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
        }

from django import forms
from .models import MedicineMaster

class MedicineMasterForm(forms.ModelForm):
    class Meta:
        model = MedicineMaster
        fields = '__all__'
        widgets = {
            'expiry_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'purchase_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super(MedicineMasterForm, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if not isinstance(field.widget, forms.DateInput):
                field.widget.attrs['class'] = 'form-control'
