from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from .forms import UserRegistrationForm, CompanyForm, MedicineForm, CustomerForm
from .models import Profile, Company, Medicine, Customer, Bill, BillDetails
from django.contrib.auth.decorators import login_required

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            Profile.objects.create(user=user, role=form.cleaned_data['role'])
            return redirect('login')
    else:
        form = UserRegistrationForm()
    return render(request, 'register.html', {'form': form})

def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('dashboard')
        else:
            error = 'Invalid credentials'
            return render(request, 'login.html', {'error': error})
    return render(request, 'login.html')

from django.shortcuts import render
from django.db.models import F, Sum, ExpressionWrapper, DecimalField
from datetime import datetime, timedelta
from .models import BillDetails, Medicine, Company, PurchaseBill

def dashboard(request):
    today = datetime.today().date()

    # Annotate BillDetails with profit
    bill_details = BillDetails.objects.annotate(
        profit=ExpressionWrapper(
            F('medicine__sell_price') - F('medicine__buy_price'),
            output_field=DecimalField()
        )
    )

    # Total Sales and Profit (all time)
    total_sales = bill_details.aggregate(
        total_amount=Sum(F('medicine__sell_price') * F('qty'), output_field=DecimalField())
    )['total_amount'] or 0

    total_profit = bill_details.aggregate(
        total_profit=Sum(F('profit') * F('qty'), output_field=DecimalField())
    )['total_profit'] or 0

    # Today's Sales and Profit
    todays_sales = bill_details.filter(added_on__date=today).aggregate(
        total_amount=Sum(F('medicine__sell_price') * F('qty'), output_field=DecimalField())
    )['total_amount'] or 0

    todays_profit = bill_details.filter(added_on__date=today).aggregate(
        total_profit=Sum(F('profit') * F('qty'), output_field=DecimalField())
    )['total_profit'] or 0

    # Expiring medicines in next 30 days
    expiry_threshold = today + timedelta(days=30)
    expiring_soon_medicines = Medicine.objects.filter(expire_date__range=(today, expiry_threshold)).count()

    # Low stock medicines
    low_stock_medicines = Medicine.objects.filter(in_stock_total__lte=10).count()

    # Additional counts for dashboard
    companies_count = Company.objects.count()
    medicines_count = Medicine.objects.count()
    purchase_bills_count = PurchaseBill.objects.count()
 

    context = {
        'total_sales': total_sales,
        'total_profit': total_profit,
        'todays_sales': todays_sales,
        'todays_profit': todays_profit,
        'expiring_soon_medicines': expiring_soon_medicines,
        'low_stock_medicines': low_stock_medicines,
        'companies_count': companies_count,
        'medicines_count': medicines_count,
        'purchase_bills_count': purchase_bills_count,
    
    }

    return render(request, 'dashboard.html', context)

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Company
from .forms import CompanyForm
@login_required
def company_list(request):
    companies = Company.objects.all().order_by('-added_on')  # Optional: Show latest first
    return render(request, 'company_list.html', {'companies': companies})


@login_required
def add_company(request):
    if request.method == 'POST':
        form = CompanyForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('company_list')
    else:
        form = CompanyForm()
    
    companies = Company.objects.all().order_by('-added_on')  # For displaying below form
    return render(request, 'add_company.html', {'form': form, 'companies': companies})


@login_required
def update_company(request, pk):
    company = get_object_or_404(Company, pk=pk)
    
    if request.method == 'POST':
        form = CompanyForm(request.POST, instance=company)
        if form.is_valid():
            form.save()
            return redirect('company_list')
    else:
        form = CompanyForm(instance=company)

    companies = Company.objects.all().order_by('-added_on')  # Optional: reuse same template
    return render(request, 'add_company.html', {'form': form, 'companies': companies})


@login_required
def delete_company(request, pk):
    company = get_object_or_404(Company, pk=pk)
    company.delete()
    return redirect('company_list')



from django.shortcuts import render, redirect, get_object_or_404
from .models import Medicine
from .forms import MedicineForm
from django.contrib.auth.decorators import login_required

@login_required
def medicine_list(request):
    medicines = Medicine.objects.all()
    return render(request, 'medicine_list.html', {'medicines': medicines})

@login_required
def add_medicine(request):
    if request.method == 'POST':
        form = MedicineForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('medicine_list')
    else:
        form = MedicineForm()
    return render(request, 'add_medicine.html', {'form': form})

@login_required
def update_medicine(request, pk):
    medicine = get_object_or_404(Medicine, pk=pk)
    if request.method == 'POST':
        form = MedicineForm(request.POST, instance=medicine)
        if form.is_valid():
            form.save()
            return redirect('medicine_list')
    else:
        form = MedicineForm(instance=medicine)
    return render(request, 'add_medicine.html', {'form': form})

@login_required
def delete_medicine(request, pk):
    medicine = get_object_or_404(Medicine, pk=pk)
    medicine.delete()
    return redirect('medicine_list')

@login_required
def user_logout(request):
    logout(request)
    return redirect('login')
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.template.loader import get_template
from weasyprint import HTML
from django.contrib.auth.decorators import login_required
import tempfile
from .models import Company, Medicine, PurchaseBill, PurchaseBillDetails

# @login_required
# def generate_purchase_bill(request):
#     companies = Company.objects.all()
#     medicines = []

#     if request.method == 'POST':
#         company_id = request.POST.get('company_id')
#         medicine_ids = request.POST.getlist('medicine_ids')
#         quantities = request.POST.getlist('quantities')

#         # Get the selected company
#         company = get_object_or_404(Company, id=company_id)
        
#         # Create a new Purchase Bill
#         bill_number = f"PB-{PurchaseBill.objects.count() + 1}"  # Generate a simple unique bill number
#         purchase_bill = PurchaseBill.objects.create(company=company, bill_number=bill_number)
        
#         total_price = 0
#         selected_meds = []

#         for med_id, qty in zip(medicine_ids, quantities):
#             if qty.strip() and int(qty) > 0:
#                 medicine = get_object_or_404(Medicine, id=med_id)
#                 quantity = int(qty)
#                 medicine_price = medicine.buy_price  # Purchase price of the medicine

#                 # Create Purchase Bill Details
#                 PurchaseBillDetails.objects.create(
#                     purchase_bill=purchase_bill,
#                     medicine=medicine,
#                     qty=quantity,
#                     medicine_price=medicine_price
#                 )

#                 total_price += medicine_price * quantity
#                 selected_meds.append({
#                     'name': medicine.name,
#                     'buy_price': medicine_price,
#                     'quantity': quantity,
#                     'total': medicine_price * quantity
#                 })

#         # Update total amount in the purchase bill
#         purchase_bill.total_amount = total_price
#         purchase_bill.save()

#         # Generate PDF using WeasyPrint
#         template = get_template('pdf_template.html')
#         html = template.render({
#             'company': company,
#             'medicines': selected_meds,
#             'total_price': total_price,
#             'bill': purchase_bill,
#         })

#         response = HttpResponse(content_type='application/pdf')
#         response['Content-Disposition'] = f'filename="purchase_bill_{purchase_bill.id}.pdf"'

#         with tempfile.NamedTemporaryFile(delete=True) as output:
#             HTML(string=html).write_pdf(target=output.name)
#             output.seek(0)
#             response.write(output.read())

#         return response

#     elif request.method == 'GET':
#         company_id = request.GET.get('company_id')
#         if company_id:
#             medicines = Medicine.objects.filter(company_id=company_id)

#     return render(request, 'generate_purchase_bill.html', {
#         'companies': companies,
#         'medicines': medicines,
#         'selected_company_id': request.GET.get('company_id', '')
#     })



from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.template.loader import get_template
from weasyprint import HTML
import tempfile
from django.contrib.auth.decorators import login_required
from .models import Company, Medicine, PurchaseBill, PurchaseBillDetails

@login_required
def generate_purchase_bill(request):
    companies = Company.objects.all()
    medicines = []

    if request.method == 'POST':
        company_id = request.POST.get('company_id')
        medicine_ids = request.POST.getlist('medicine_ids')
        quantities = request.POST.getlist('quantities')

        # Get the selected company
        company = get_object_or_404(Company, id=company_id)
        
        # Create a new Purchase Bill
        bill_number = f"PB-{PurchaseBill.objects.count() + 1}"  # Generate a simple unique bill number
        purchase_bill = PurchaseBill.objects.create(company=company, bill_number=bill_number)
        
        total_price = 0
        selected_meds = []

        for med_id, qty in zip(medicine_ids, quantities):
            if qty.strip() and int(qty) > 0:
                medicine = get_object_or_404(Medicine, id=med_id)
                quantity = int(qty)
                medicine_price = medicine.buy_price  # Purchase price of the medicine

                # Create Purchase Bill Details
                PurchaseBillDetails.objects.create(
                    purchase_bill=purchase_bill,
                    medicine=medicine,
                    qty=quantity,
                    medicine_price=medicine_price
                )

                # # Update medicine stock after purchase
                # if medicine.in_stock_total >= quantity:
                medicine.in_stock_total += quantity  # Increase the stock after purchase
                medicine.save()

                total_price += medicine_price * quantity
                selected_meds.append({
                    'name': medicine.name,
                    'buy_price': medicine_price,
                    'quantity': quantity,
                    'total': medicine_price * quantity
                })

        # Update total amount in the purchase bill
        purchase_bill.total_amount = total_price
        purchase_bill.save()

        # Generate PDF using WeasyPrint
        return render(request, 'pdf_template.html', { 'company': company,
            'medicines': selected_meds,
            'total_price': total_price,
            'bill': purchase_bill,})
        # template = get_template('pdf_template.html')
        # html = template.render({
        #     'company': company,
        #     'medicines': selected_meds,
        #     'total_price': total_price,
        #     'bill': purchase_bill,
        # })

        # response = HttpResponse(content_type='application/pdf')
        # response['Content-Disposition'] = f'filename="purchase_bill_{purchase_bill.id}.pdf"'

        # with tempfile.NamedTemporaryFile(delete=True) as output:
        #     HTML(string=html).write_pdf(target=output.name)
        #     output.seek(0)
        #     response.write(output.read())

        # return response

    elif request.method == 'GET':
        company_id = request.GET.get('company_id')
        if company_id:
            medicines = Medicine.objects.filter(company_id=company_id)

    return render(request, 'generate_purchase_bill.html', {
        'companies': companies,
        'medicines': medicines,
        'selected_company_id': request.GET.get('company_id', '')
    })


from django.http import JsonResponse
@login_required
def get_medicines_by_company(request):
    company_id = request.GET.get('company_id')
    medicines = Medicine.objects.filter(company_id=company_id).values('id', 'name', 'buy_price')
    return JsonResponse(list(medicines), safe=False)


from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Medicine, Customer, Bill, BillDetails

from django.http import HttpResponse
from django.template.loader import get_template
from weasyprint import HTML
import tempfile
from .models import Bill, BillDetails, Medicine, Customer
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required

# @login_required
# def generate_sale_bill(request):
#     if request.method == 'POST':
#         # Get customer details
#         customer_name = request.POST.get('customerName')
#         address = request.POST.get('address')
#         phone = request.POST.get('phone')

#         # Find or create the customer
#         customer, created = Customer.objects.get_or_create(
#             name=customer_name,
#             address=address,
#             contact=phone
#         )

#         # Get medicine data
#         medicine_ids = request.POST.getlist('medicine_ids[]')
#         quantities = request.POST.getlist('quantities[]')

#         # Create bill
#         bill = Bill.objects.create(customer=customer)
#         total_price = 0

#         for medicine_id, quantity in zip(medicine_ids, quantities):
#             medicine = get_object_or_404(Medicine, id=medicine_id)
#             qty = int(quantity)
#             total_price += medicine.sell_price * qty

#             # Create bill detail
#             BillDetails.objects.create(
#                 bill=bill,
#                 medicine=medicine,
#                 qty=qty,
#             )

#         # Render the HTML template for the sale bill
#         template = get_template('pdf_template.html')  # Ensure you have a template named 'pdf_template.html'
#         html = template.render({
#             'bill': bill,
#             'total_price': total_price,
#             'customer': customer,
#             'items': BillDetails.objects.filter(bill=bill),
#         })

#         # Generate PDF response
#         response = HttpResponse(content_type='application/pdf')
#         response['Content-Disposition'] = f'inline; filename="sale_bill_{bill.id}.pdf"'

#         with tempfile.NamedTemporaryFile(delete=True) as output:
#             HTML(string=html).write_pdf(target=output.name)
#             output.seek(0)
#             response.write(output.read())

#         return response

#     # GET request - show the form for creating the sale bill
#     medicines = Medicine.objects.all()
#     return render(request, 'generate_sale_bill.html', {'medicines': medicines})
@login_required
def generate_sale_bill(request):
    if request.method == 'POST':
        # Get customer details
        customer_name = request.POST.get('customerName')
        address = request.POST.get('address')
        phone = request.POST.get('phone')

        # Find or create the customer
        customer, created = Customer.objects.get_or_create(
            name=customer_name,
            address=address,
            contact=phone
        )

        # Get medicine data
        medicine_ids = request.POST.getlist('medicine_ids[]')
        quantities = request.POST.getlist('quantities[]')

        # Create bill
        bill = Bill.objects.create(customer=customer)
        total_price = 0
        item_totals = []

        for medicine_id, quantity in zip(medicine_ids, quantities):
            medicine = get_object_or_404(Medicine, id=medicine_id)
            qty = int(quantity)

            # Check if enough stock is available
            if medicine.in_stock_total < qty:
                messages.error(request, f"Not enough stock for {medicine.name}. Available: {medicine.in_stock_total}")
                return redirect('generate_sale_bill')

            # Calculate total price for this item
            item_total = medicine.sell_price * qty
            total_price += item_total

            # Create bill detail
            BillDetails.objects.create(
                bill=bill,
                medicine=medicine,
                qty=qty,
            )
            item_totals.append({
                'medicine': medicine,
                'qty': qty,
                'item_total': item_total
            })

            # Reduce stock after sale
            medicine.in_stock_total -= qty
            medicine.save()

        # Render the HTML template for the sale bill
        template = get_template('pdf_template1.html')
        html = template.render({
            'bill': bill,
            'total_price': total_price,
            'customer': customer,
            'items': item_totals,
        })

        # Generate PDF response
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="sale_bill_{bill.id}.pdf"'

        with tempfile.NamedTemporaryFile(delete=True) as output:
            HTML(string=html).write_pdf(target=output.name)
            output.seek(0)
            response.write(output.read())

        return response

    # GET request - show the form for creating the sale bill
    medicines = Medicine.objects.all()
    return render(request, 'generate_sale_bill.html', {'medicines': medicines})

from django.shortcuts import render
from .models import PurchaseBill, Bill
from django.db.models import Sum
from datetime import datetime

from django.db.models import Sum
from django.shortcuts import render
from .models import PurchaseBill

from django.shortcuts import render
from django.db.models import Sum, F, DecimalField, ExpressionWrapper
from .models import PurchaseBill

def purchase_history(request):
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')

    # Prefetch related fields to avoid extra DB hits
    purchase_bills = PurchaseBill.objects.prefetch_related('purchasebilldetails_set__medicine', 'company')

    # Filter by date range if provided
    if from_date and to_date:
        purchase_bills = purchase_bills.filter(added_on__date__range=[from_date, to_date])

    # Recalculate total amount (in case some are not updated)
    for bill in purchase_bills:
        total = 0
        for item in bill.purchasebilldetails_set.all():
            item.total_price = item.medicine_price * item.qty  # Adding total_price dynamically for display
            total += item.total_price
        bill.calculated_total = total  # Dynamic field for display (doesn't override DB)

    # Calculate total purchase amount for all filtered bills
    total_amount = sum(bill.calculated_total for bill in purchase_bills)

    return render(request, 'purchase_history.html', {
        'purchase_bills': purchase_bills,
        'from_date': from_date,
        'to_date': to_date,
        'total_amount': total_amount,
    })

def sales_history(request):
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')

    bills = Bill.objects.all()
    if from_date and to_date:
        bills = bills.filter(added_on__date__range=[from_date, to_date])

    # Filter out bills with zero amount and zero profit
    filtered_bills = [b for b in bills if b.total_amount() != 0 or b.total_profit() != 0]

    total_amount = sum(b.total_amount() for b in filtered_bills)
    total_profit = sum(b.total_profit() for b in filtered_bills)

    return render(request, 'sales_history.html', {
        'bills': filtered_bills,
        'from_date': from_date,
        'to_date': to_date,
        'total_amount': total_amount,
        'total_profit': total_profit,
    })
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import PurchaseHistory
from decimal import Decimal, InvalidOperation
from datetime import date

# Create View
def create_purchase(request):
    if request.method == 'POST':
        try:
            # Extract and sanitize input data
            medicine_name = request.POST.get('medicine_name', '').strip()
            medicine_type = request.POST.get('medicine_type', '').strip().lower()
            pack_quantity = request.POST.get('pack_quantity')
            qty_per_strip = request.POST.get('qty_per_strip')
            free_medicine_qty = request.POST.get('free_medicine_qty', 0)
            company_name = request.POST.get('company_name', '').strip()
            expiry_date = request.POST.get('expiry_date')
            mrp_rate = request.POST.get('mrp_rate')
            shop_rate = request.POST.get('shop_rate')

            # Validation for required fields
            if not all([medicine_name, medicine_type, pack_quantity, qty_per_strip, company_name, expiry_date, mrp_rate, shop_rate]):
                messages.error(request, "All fields except 'Free Medicine Quantity' are required.")
                return redirect('create_purchase')

            # Medicine type validation
            valid_types = ['tablet', 'cream/jel', 'liquid']
            if medicine_type not in valid_types:
                messages.error(request, "Invalid medicine type. Choose from Tablet, Cream/Jel, or Liquid.")
                return redirect('create_purchase')

            # Type conversion and validations
            try:
                pack_quantity = int(pack_quantity)
                qty_per_strip = int(qty_per_strip)
                free_medicine_qty = int(free_medicine_qty)
                mrp_rate = Decimal(mrp_rate)
                shop_rate = Decimal(shop_rate)
                expiry = date.fromisoformat(expiry_date)
            except (ValueError, InvalidOperation):
                messages.error(request, "Invalid numeric or date input. Please check your entries.")
                return redirect('create_purchase')

            if pack_quantity <= 0 or qty_per_strip <= 0:
                messages.error(request, "Pack quantity and quantity per strip must be greater than 0.")
                return redirect('create_purchase')

            if free_medicine_qty < 0:
                messages.error(request, "Free medicine quantity cannot be negative.")
                return redirect('create_purchase')

            if expiry < date.today():
                messages.error(request, "Expiry date must be today or in the future.")
                return redirect('create_purchase')

            if mrp_rate < shop_rate:
                messages.error(request, "MRP cannot be less than shop rate.")
                return redirect('create_purchase')

            # Calculate total amount
            total_amount = Decimal(qty_per_strip) * shop_rate

            # Save the new purchase entry
            new_purchase = PurchaseHistory(
                medicine_name=medicine_name,
                medicine_type=medicine_type,
                pack_quantity=pack_quantity,
                qty_per_strip=qty_per_strip,
                free_medicine_qty=free_medicine_qty,
                company_name=company_name,
                expiry_date=expiry,
                mrp_rate=mrp_rate,
                shop_rate=shop_rate,
                total_amount=total_amount
            )
            new_purchase.save()

            messages.success(request, "Purchase history created successfully!")
            return redirect('create_purchase')

        except Exception as e:
            messages.error(request, f"Unexpected error: {str(e)}")
            return redirect('create_purchase')

    purchases = PurchaseHistory.objects.all().order_by('-id')  # Fetching recent entries
    return render(request, 'purchase_form_manual.html', {'purchases': purchases})

# Edit View
def edit_purchase(request, pk):
    purchase = get_object_or_404(PurchaseHistory, pk=pk)

    if request.method == 'POST':
        try:
            # Extract and sanitize input data
            medicine_name = request.POST.get('medicine_name', '').strip()
            medicine_type = request.POST.get('medicine_type', '').strip().lower()
            pack_quantity = request.POST.get('pack_quantity')
            qty_per_strip = request.POST.get('qty_per_strip')
            free_medicine_qty = request.POST.get('free_medicine_qty', 0)
            company_name = request.POST.get('company_name', '').strip()
            expiry_date = request.POST.get('expiry_date')
            mrp_rate = request.POST.get('mrp_rate')
            shop_rate = request.POST.get('shop_rate')

            # Validation for required fields
            if not all([medicine_name, medicine_type, pack_quantity, qty_per_strip, company_name, expiry_date, mrp_rate, shop_rate]):
                messages.error(request, "All fields except 'Free Medicine Quantity' are required.")
                return redirect('edit_purchase', pk=pk)

            # Medicine type validation
            valid_types = ['tablet', 'cream/jel', 'liquid']
            if medicine_type not in valid_types:
                messages.error(request, "Invalid medicine type. Choose from Tablet, Cream/Jel, or Liquid.")
                return redirect('edit_purchase', pk=pk)

            # Type conversion and validations
            try:
                pack_quantity = int(pack_quantity)
                qty_per_strip = int(qty_per_strip)
                free_medicine_qty = int(free_medicine_qty)
                mrp_rate = Decimal(mrp_rate)
                shop_rate = Decimal(shop_rate)
                expiry = date.fromisoformat(expiry_date)
            except (ValueError, InvalidOperation):
                messages.error(request, "Invalid numeric or date input. Please check your entries.")
                return redirect('edit_purchase', pk=pk)

            if pack_quantity <= 0 or qty_per_strip <= 0:
                messages.error(request, "Pack quantity and quantity per strip must be greater than 0.")
                return redirect('edit_purchase', pk=pk)

            if free_medicine_qty < 0:
                messages.error(request, "Free medicine quantity cannot be negative.")
                return redirect('edit_purchase', pk=pk)

            if expiry < date.today():
                messages.error(request, "Expiry date must be today or in the future.")
                return redirect('edit_purchase', pk=pk)

            if mrp_rate < shop_rate:
                messages.error(request, "MRP cannot be less than shop rate.")
                return redirect('edit_purchase', pk=pk)

            # Calculate total amount
            total_amount = Decimal(qty_per_strip) * shop_rate
            print(total_amount,"_________")

            # Update the record
            purchase.medicine_name = medicine_name
            purchase.medicine_type = medicine_type
            purchase.pack_quantity = pack_quantity
            purchase.qty_per_strip = qty_per_strip
            purchase.free_medicine_qty = free_medicine_qty
            purchase.company_name = company_name
            purchase.expiry_date = expiry
            purchase.mrp_rate = mrp_rate
            purchase.shop_rate = shop_rate
            purchase.total_amount = total_amount
            purchase.save()

            messages.success(request, "Purchase history updated successfully!")
            return redirect('create_purchase')  # Redirect to the page you want after updating

        except Exception as e:
            messages.error(request, f"Unexpected error: {str(e)}")
            return redirect('edit_purchase', pk=pk)

    return render(request, 'purchase_edit_form.html', {'purchase': purchase})

# Delete View
def delete_purchase(request, pk):
    purchase = get_object_or_404(PurchaseHistory, pk=pk)

    if request.method == 'POST':
        purchase.delete()
        messages.success(request, "Purchase history deleted successfully!")
        return redirect('create_purchase')

    return render(request, 'purchase_confirm_delete.html', {'purchase': purchase})
from django.shortcuts import render, redirect
from django.http import JsonResponse
from .models import PurchaseHistory, SalesRegister
from django.views.decorators.csrf import csrf_exempt

def sales_register_view(request):
    medicines = PurchaseHistory.objects.all()
    sale_details = None  # Initialize to None, in case there's no sale yet.
    sales = SalesRegister.objects.all()  # Get all sales for the table

    if request.method == "POST":
        customer_name = request.POST.get("customer_name")
        medicine_id = request.POST.get("medicine")
        qty_strips = int(request.POST.get("qty_strips") or 0)
        qty_loose = int(request.POST.get("qty_loose") or 0)
        discount = float(request.POST.get("discount") or 0)

        medicine = PurchaseHistory.objects.get(id=medicine_id)
        rate_strip = float(medicine.mrp_rate)
        rate_loose = rate_strip / medicine.qty_per_strip
        total = (qty_strips * rate_strip) + (qty_loose * rate_loose) - discount

        # Save the sale in the SalesRegister
        sale = SalesRegister.objects.create(
            customer_name=customer_name,
            medicine=medicine,
            qty_strips=qty_strips,
            qty_loose=qty_loose,
            discount=discount,
            total_amount=round(total, 2),
        )

        # Prepare the sale details to show the bill on the page
        sale_details = {
            "customer_name": sale.customer_name,
            "medicine": sale.medicine.medicine_name,
            "qty_strips": sale.qty_strips,
            "qty_loose": sale.qty_loose,
            "discount": sale.discount,
            "total_amount": sale.total_amount,
        }

    return render(request, "sales_register.html", {"medicines": medicines, "sale_details": sale_details, "sales": sales})

@csrf_exempt
def get_medicine_details(request):
    if request.method == "POST":
        med_id = request.POST.get("medicine_id")
        medicine = PurchaseHistory.objects.get(id=med_id)
        rate_loose = float(medicine.mrp_rate) / medicine.pack_quantity
        return JsonResponse({
            "rate_per_strip": float(medicine.mrp_rate),
            "rate_per_loose": round(rate_loose, 2),
            "qty_per_strip": medicine.qty_per_strip
        })
