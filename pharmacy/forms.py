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
        fields = ['medicine_name', 'medicine_type', 'pack_quantity', 'qty_per_strip', 'free_medicine_qty', 'company_name', 'expiry_date', 'mrp_rate', 'shop_rate']
        widgets = {
            'expiry_date': forms.DateInput(attrs={'type': 'date'}),
        }
