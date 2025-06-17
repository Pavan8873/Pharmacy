from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from .forms import UserRegistrationForm, CompanyForm, MedicineForm, CustomerForm
from .models import Profile, Company, Medicine, Customer, Bill1, BillDetails
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
from .models import PurchaseHistory, SalesRegister

def dashboard(request):
    today = datetime.today().date()

    # Annotate SalesRegister with profit
    sales_register = SalesRegister.objects.annotate(
        profit=ExpressionWrapper(
            F('medicine__mrp_rate') - F('medicine__shop_rate'),
            output_field=DecimalField()
        )
    )

    # Total Sales and Profit (all time)
    total_sales = sales_register.aggregate(
        total_amount=Sum(F('total_amount'), output_field=DecimalField())
    )['total_amount'] or 0

    total_profit = sales_register.aggregate(
        total_profit=Sum(F('profit') * F('qty_in_strips') + F('profit') * F('qty_in_loose'), output_field=DecimalField())
    )['total_profit'] or 0

    # Today's Sales and Profit
    todays_sales = sales_register.filter(sale_date__date=today).aggregate(
        total_amount=Sum(F('total_amount'), output_field=DecimalField())
    )['total_amount'] or 0

    todays_profit = sales_register.filter(sale_date__date=today).aggregate(
        total_profit=Sum(F('profit') * F('qty_in_strips') + F('profit') * F('qty_in_loose'), output_field=DecimalField())
    )['total_profit'] or 0

    # Expiring medicines in next 30 days
    expiry_threshold = today + timedelta(days=30)
    # expiring_soon_medicines = MedicineMaster.objects.filter(expiry_date__range=(today, expiry_threshold)).count()

    # # Low stock medicines (low stock condition is assumed to be quantity < 10)
    # low_stock_medicines = MedicineMaster.objects.filter(qty_in_strip__lte=10).count()

    # # Get the list of medicines with their names and quantities (pack_quantity)
    # medicines_list = MedicineMaster.objects.values('medicine_name', 'Number_of_medicines_per_strip')

    # Additional counts for dashboard
    
    total_sales_count = SalesRegister.objects.count()

    context = {
        'total_sales': total_sales,
        'total_profit': total_profit,
        'todays_sales': todays_sales,
        'todays_profit': todays_profit,
        # 'expiring_soon_medicines': expiring_soon_medicines,
        # 'low_stock_medicines': low_stock_medicines,
        # 'medicines_list': medicines_list.count(),  # Passing medicine names and quantities
        'total_sales_count': total_sales_count,
    }

    return render(request, 'dashboard.html', context)


from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import PurchaseHistory

@login_required
def company_list(request):
    companies = (
        PurchaseHistory.objects
        .values('company_name')
        .distinct()
        .order_by('company_name')
    )
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
    print("____________________________")
    medicines = MedicineMaster.objects.all()
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
# from django.shortcuts import render, redirect
# from django.contrib import messages
# from .models import PurchaseHistory, MedicineMaster
# from decimal import Decimal, InvalidOperation
# from datetime import date

# # Create View
# def create_purchase(request):
#     if request.method == 'POST':
#         try:
#             # Extract and sanitize input data
#             medicine_name = request.POST.get('medicine_name', '').strip()
#             medicine_type = request.POST.get('medicine_type', '').strip().lower()
#             pack_quantity = request.POST.get('pack_quantity')
#             qty_per_strip = request.POST.get('qty_per_strip')
#             free_medicine_qty = request.POST.get('free_medicine_qty', 0)
#             company_name = request.POST.get('company_name', '').strip()
#             expiry_date = request.POST.get('expiry_date')
#             mrp_rate = request.POST.get('mrp_rate')
#             shop_rate = request.POST.get('shop_rate')

#             # Validation for required fields
#             if not all([medicine_name, medicine_type, pack_quantity, qty_per_strip, company_name, expiry_date, mrp_rate, shop_rate]):
#                 messages.error(request, "All fields except 'Free Medicine Quantity' are required.")
#                 return redirect('create_purchase')

#             # Medicine type validation
#             valid_types = ['tablet', 'cream/jel', 'liquid']
#             if medicine_type not in valid_types:
#                 messages.error(request, "Invalid medicine type. Choose from Tablet, Cream/Jel, or Liquid.")
#                 return redirect('create_purchase')

#             # Type conversion and validations
#             try:
#                 pack_quantity = int(pack_quantity)
#                 qty_per_strip = int(qty_per_strip)
#                 free_medicine_qty = int(free_medicine_qty)
#                 mrp_rate = Decimal(mrp_rate)
#                 shop_rate = Decimal(shop_rate)
#                 expiry = date.fromisoformat(expiry_date)
#             except (ValueError, InvalidOperation):
#                 messages.error(request, "Invalid numeric or date input. Please check your entries.")
#                 return redirect('create_purchase')

#             # if pack_quantity <= 0 or qty_per_strip <= 0:
#             #     messages.error(request, "Pack quantity and quantity per strip must be greater than 0.")
#             #     return redirect('create_purchase')

#             if free_medicine_qty < 0:
#                 messages.error(request, "Free medicine quantity cannot be negative.")
#                 return redirect('create_purchase')

#             if expiry < date.today():
#                 messages.error(request, "Expiry date must be today or in the future.")
#                 return redirect('create_purchase')

#             if mrp_rate < shop_rate:
#                 messages.error(request, "MRP cannot be less than shop rate.")
#                 return redirect('create_purchase')

#             # Calculate total amount for the purchase
#             total_amount = Decimal(shop_rate * qty_per_strip)

#             # Save the new purchase entry in the PurchaseHistory table
#             new_purchase = PurchaseHistory(
#                 medicine_name=medicine_name,
#                 medicine_type=medicine_type,
#                 Number_of_medicines_per_strip=pack_quantity,
#                 qty_in_strip=qty_per_strip,
#                 free_medicine_qty=free_medicine_qty,
#                 company_name=company_name,
#                 expiry_date=expiry,
#                 mrp_rate=mrp_rate,
#                 shop_rate=shop_rate,
#                 total_amount=total_amount
#             )
#             new_purchase.save()

#             # Check if this medicine already exists in the MedicineMaster table
#             x=qty_per_strip+free_medicine_qty
#             medicine_master, created = MedicineMaster.objects.get_or_create(
#                 medicine_name=medicine_name,
#                 medicine_type=medicine_type,
#                 company_name=company_name,
#                 defaults={
#                     'expiry_date': expiry,
#                     'mrp_rate': mrp_rate,
#                     'shop_rate': shop_rate,
#                     'Number_of_medicines_per_strip': pack_quantity,
#                     'qty_in_strip': x,
       
#                     'total_amount': total_amount,
#                 }
#             )

#             # If the medicine already exists, update the stock and quantity
#             if not created:
#                 medicine_master.Number_of_medicines_per_strip += pack_quantity
#                 medicine_master.qty_in_strip = qty_per_strip
        
#                 medicine_master.total_amount += total_amount
#                 medicine_master.save()

#             messages.success(request, "Purchase history created successfully, and Medicine Master updated!")
#             return redirect('create_purchase')

#         except Exception as e:
#             messages.error(request, f"Unexpected error: {str(e)}")
#             return redirect('create_purchase')

#     # Fetch all purchases and order by recent entries
#     purchases = PurchaseHistory.objects.all().order_by('-id')
#     return render(request, 'purchase_form_manual.html', {'purchases': purchases})
# from django.shortcuts import render, redirect, get_object_or_404
# from django.contrib import messages
# from .models import PurchaseHistory, MedicineMaster
# from decimal import Decimal, InvalidOperation
# from datetime import date

# # Edit View
# def edit_purchase(request, pk):
#     purchase = get_object_or_404(PurchaseHistory, pk=pk)
#     print(purchase.expiry_date)

#     if request.method == 'POST':
#         try:
#             # Extract and sanitize input data
#             medicine_name = request.POST.get('medicine_name', '').strip()
#             medicine_type = request.POST.get('medicine_type', '').strip().lower()
#             pack_quantity = request.POST.get('pack_quantity')
#             qty_per_strip = request.POST.get('qty_per_strip')
#             free_medicine_qty = request.POST.get('free_medicine_qty', 0)
#             company_name = request.POST.get('company_name', '').strip()
#             expiry_date = request.POST.get('expiry_date')
#             mrp_rate = request.POST.get('mrp_rate')
#             shop_rate = request.POST.get('shop_rate')

#             # Validation for required fields
#             if not all([medicine_name, medicine_type, pack_quantity, qty_per_strip, company_name, expiry_date, mrp_rate, shop_rate]):
#                 messages.error(request, "All fields except 'Free Medicine Quantity' are required.")
#                 return redirect('edit_purchase', pk=pk)

#             # Medicine type validation
#             valid_types = ['tablet', 'cream/jel', 'liquid']
#             if medicine_type not in valid_types:
#                 messages.error(request, "Invalid medicine type. Choose from Tablet, Cream/Jel, or Liquid.")
#                 return redirect('edit_purchase', pk=pk)

#             # Type conversion and validations
#             try:
#                 pack_quantity = int(pack_quantity)
#                 qty_per_strip = int(qty_per_strip)
#                 free_medicine_qty = int(free_medicine_qty)
#                 mrp_rate = Decimal(mrp_rate)
#                 shop_rate = Decimal(shop_rate)
#                 expiry = date.fromisoformat(expiry_date)
#             except (ValueError, InvalidOperation):
#                 messages.error(request, "Invalid numeric or date input. Please check your entries.")
#                 return redirect('edit_purchase', pk=pk)

#             # if pack_quantity <= 0 or qty_per_strip <= 0:
#             #     messages.error(request, "Pack quantity and quantity per strip must be greater than 0.")
#             #     return redirect('edit_purchase', pk=pk)

#             if free_medicine_qty < 0:
#                 messages.error(request, "Free medicine quantity cannot be negative.")
#                 return redirect('edit_purchase', pk=pk)

#             if expiry < date.today():
#                 messages.error(request, "Expiry date must be today or in the future.")
#                 return redirect('edit_purchase', pk=pk)

#             if mrp_rate < shop_rate:
#                 messages.error(request, "MRP cannot be less than shop rate.")
#                 return redirect('edit_purchase', pk=pk)

#             # Calculate total amount
#             total_amount = Decimal(qty_per_strip+free_medicine_qty) * shop_rate 

#             # Update the record in PurchaseHistory
#             purchase.medicine_name = medicine_name
#             purchase.medicine_type = medicine_type
#             purchase.Number_of_medicines_per_strip = pack_quantity
#             purchase.qty_in_strip = qty_per_strip
#             purchase.free_medicine_qty = free_medicine_qty
#             purchase.company_name = company_name
#             purchase.expiry_date = expiry
#             purchase.mrp_rate = mrp_rate
#             purchase.shop_rate = shop_rate
#             purchase.total_amount = total_amount
#             purchase.save()

#             # Update the corresponding MedicineMaster record
#             medicine_master, created = MedicineMaster.objects.get_or_create(
#                 medicine_name=medicine_name,
#                 medicine_type=medicine_type,
#                 company_name=company_name
#             )

#             # Update the MedicineMaster fields
#             medicine_master.expiry_date = expiry
#             medicine_master.mrp_rate = mrp_rate
#             medicine_master.shop_rate = shop_rate
#             medicine_master.Number_of_medicines_per_strip = pack_quantity
#             medicine_master.qty_in_strip = qty_per_strip+free_medicine_qty
          
#             medicine_master.total_amount = total_amount
#             medicine_master.save()

#             messages.success(request, "Purchase history and Medicine Master updated successfully!")
#             return redirect('create_purchase')  # Redirect to the page you want after updating

#         except Exception as e:
#             messages.error(request, f"Unexpected error: {str(e)}")
#             return redirect('edit_purchase', pk=pk)

#     return render(request, 'purchase_edit_form.html', {'purchase': purchase})

# # Delete View
# def delete_purchase(request, pk):
#     purchase = get_object_or_404(PurchaseHistory, pk=pk)

#     if request.method == 'POST':
#         # Fetch the corresponding MedicineMaster record
#         medicine_master = MedicineMaster.objects.filter(
#             medicine_name=purchase.medicine_name,
#             medicine_type=purchase.medicine_type,
#             company_name=purchase.company_name
#         ).first()

#         # If the medicine exists in MedicineMaster, update or delete it
#         if medicine_master:
#             # Decrease the stock quantities or delete the record if necessary
#             medicine_master.Number_of_medicines_per_strip -= purchase.Number_of_medicines_per_strip


#             # If stock reaches zero, delete the record from MedicineMaster
#             if medicine_master.Number_of_medicines_per_strip <= 0:
#                 medicine_master.delete()
#             else:
#                 medicine_master.save()

#         # Delete the purchase entry from PurchaseHistory
#         purchase.delete()
#         messages.success(request, "Purchase history and Medicine Master updated successfully!")
#         return redirect('create_purchase')

#     return render(request, 'purchase_confirm_delete.html', {'purchase': purchase})
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import PurchaseHistory, MedicineMaster, Bill
from decimal import Decimal
from datetime import date, datetime
from django.db.models import Prefetch
from decimal import Decimal

def create_purchase(request):
    bill_number = f"BILL{date.today().strftime('%Y%m%d')}-{str(Bill1.objects.count() + 1).zfill(4)}"
    # Retrieve all bills and their associated purchases
    filter_date_str = request.GET.get('filter_date')
    bills_qs = Bill1.objects.prefetch_related('purchases').all()
    medicines = MedicineMaster.objects.all()
    vendors = Vendor.objects.all()

    if filter_date_str:
        try:
            filter_date = datetime.strptime(filter_date_str, '%Y-%m-%d').date()
            # 2️⃣ Find purchase histories on that date
            ph_qs = PurchaseHistory.objects.filter(purchase_date=filter_date)
            # 3️⃣ Extract distinct bill IDs
            bill_ids = ph_qs.values_list('bill_id', flat=True).distinct()
            # 4️⃣ Limit your bills queryset
            bills_qs = bills_qs.filter(id__in=bill_ids)
        except ValueError:
            # invalid date, fall back to all bills
            pass

    context = {
        'bill_number': bill_number,
        'purchase_bills': bills_qs,
        'selected_filter_date': filter_date_str,
        'medicines':medicines,
        'vendors':vendors
    }
    # if request.method == 'POST':
    #     try:
    #         company_name = request.POST.get('company_name', '').strip()
    #         bill_date_str = request.POST.get('bill_date')
    #         payment_mode = request.POST.get('payment_mode')
    #         cheque_number = request.POST.get('cheque_number', '') if payment_mode == 'cheque' else ''
    #         cheque_date_str = request.POST.get('cheque_date', '') if payment_mode == 'cheque' else None

    #         medicine_names = request.POST.getlist('medicine_name[]')
    #         quantities = request.POST.getlist('quantity[]')
    #         freequantities_list = request.POST.getlist('freequantity[]')
    #         batch_numbers = request.POST.getlist('batch_number[]')
    #         expiry_dates_str = request.POST.getlist('expiry_date[]')
    #         mrp_rates_str = request.POST.getlist('mrp[]')
    #         purchase_rates_str = request.POST.getlist('purchase_rate[]')

    #         # Compute total bill manually instead of using posted value
    #         total_bill_amount = Decimal('0.00')

    #         bill = Bill1.objects.create(
    #             bill_number=bill_number,
    #             bill_date=bill_date_str,
    #             bill_amount=Decimal('0.00'),  # temporary, will update later
    #             payment_status='pending',
    #             payment_mode='',
    #             cheque_number='',
    #             cheque_date='',
    #             combined_pay=''
    #         )

    #         for i in range(len(medicine_names)):
    #             medicine_name = medicine_names[i]
    #             batch_number = batch_numbers[i] if i < len(batch_numbers) else ''
    #             qty = int(quantities[i]) if i < len(quantities) and quantities[i] else 0
    #             free_qty = int(freequantities_list[i]) if i < len(freequantities_list) and freequantities_list[i] else 0
    #             purchase_rate = Decimal(purchase_rates_str[i]) if i < len(purchase_rates_str) and purchase_rates_str[i] else Decimal('0.00')
    #             mrp_rate = Decimal(mrp_rates_str[i]) if i < len(mrp_rates_str) and mrp_rates_str[i] else Decimal('0.00')
    #             expiry_date_str = expiry_dates_str[i] if i < len(expiry_dates_str) and expiry_dates_str[i] else None
    #             expiry_date = datetime.strptime(expiry_date_str, '%Y-%m-%d').date() if expiry_date_str else None

    #             amount = (qty + free_qty) * purchase_rate
    #             total_bill_amount += amount

    #             PurchaseHistory.objects.create(
    #                 bill=bill,
    #                 batch_number=batch_number,
    #                 medicine_name=medicine_name,
    #                 qty_in_strip=qty,
    #                 free_medicine_qty=free_qty,
    #                 company_name=company_name,
    #                 expiry_date=expiry_date,
    #                 mrp_rate=mrp_rate,
    #                 shop_rate=purchase_rate,
    #                 total_amount=amount,
    #                 purchase_date=date.today()
    #             )

    #         bill.bill_amount = total_bill_amount
    #         bill.save()

    #         messages.success(request, "Purchase record successfully created!")
    #         return redirect('purchase_bill_details')

    #     except Exception as e:
    #         messages.error(request, f"Error occurred: {e}")
    #         return render(request, 'purchase_form_manual.html', context)
    if request.method == 'POST':
        try:
            company_name = request.POST.get('company_name', '').strip()
            bill_date_str = request.POST.get('bill_date')
            payment_mode = request.POST.get('payment_mode')
            cheque_number = request.POST.get('cheque_number', '') if payment_mode == 'cheque' else ''
            cheque_date_str = request.POST.get('cheque_date', '') if payment_mode == 'cheque' else None

            medicine_names = request.POST.getlist('medicine_name[]')
            
            quantities = request.POST.getlist('quantity[]')
            freequantities_list = request.POST.getlist('freequantity[]')
      
            batch_numbers = request.POST.getlist('batch_number[]')
          
            expiry_dates_str = request.POST.getlist('expiry_date[]')
            mrp_rates_str = request.POST.getlist('mrp[]')
            purchase_rates_str = request.POST.getlist('purchase_rate[]')



            
            total_bill_amount = Decimal('0.00')



            bill = Bill1.objects.create(
                bill_number=bill_number,
                bill_date=bill_date_str,
                bill_amount=total_bill_amount,
                payment_status='pending',      # always pending on creation
                payment_mode='',               # empty string for CharField OK
                cheque_number='',              # empty string for CharField OK
                cheque_date=None,    
                combined_pay=''           # use None for DateField to be blank
            )


     
            for i in range(len(medicine_names)):
                print("_++_+_+")
                medicine_name = medicine_names[i]
               
               
                batch_number = batch_numbers[i] if i < len(batch_numbers) else ''
                qty = int(quantities[i]) if i < len(quantities) and quantities[i] else 0
                free_qty = int(freequantities_list[i]) if i < len(freequantities_list) and freequantities_list[i] else 0
                purchase_rate = Decimal(purchase_rates_str[i]) if i < len(purchase_rates_str) and purchase_rates_str[i] else Decimal('0.00')
                
                mrp_rate = Decimal(mrp_rates_str[i]) if i < len(mrp_rates_str) and mrp_rates_str[i] else Decimal('0.00')
                expiry_date_str = expiry_dates_str[i] if i < len(expiry_dates_str) and expiry_dates_str[i] else None
               

                expiry_date = datetime.strptime(expiry_date_str, '%Y-%m-%d').date() if expiry_date_str else None
                amount = (qty) * purchase_rate 
                total_bill_amount += amount

                PurchaseHistory.objects.create(
                    bill=bill,
                    batch_number=batch_number,
                    medicine_name=medicine_name,
                    qty_in_strip=qty+free_qty,
                    free_medicine_qty=free_qty,
                    company_name=company_name,
                    expiry_date=expiry_date,
                    mrp_rate=mrp_rate,
                    shop_rate=purchase_rate,
                    total_amount=amount,
                    purchase_date=date.today(),  # ✅ Set today's date,
                    qty_in_strip_history=qty,
                    free_medicine_qty_history=free_qty

                    
                )

               


            bill.bill_amount = total_bill_amount
            bill.save()

            messages.success(request, "Purchase record successfully created!")
            return redirect('purchase_bill_details')
        except Exception as e:
            messages.error(request, f"Error occurred: {e}")
            return render(request, 'purchase_form_manual.html', context)
        
        

    return render(request, 'purchase_form_manual.html', context)
# purchase_app/views.py
from django.shortcuts import render, get_object_or_404
from .models import Bill1, PurchaseHistory

def purchase_bill_details(request, bill_id):
    """View to display details of a specific purchase bill and its associated medicines."""
    bill = get_object_or_404(Bill1, id=bill_id)
    purchase_items = PurchaseHistory.objects.filter(bill=bill)

    vendor_name = purchase_items.first().company_name if purchase_items.exists() else "Unknown Vendor"
    context = {
        'bill': bill,
        'purchase_items': purchase_items,
        'vendor_name':vendor_name
    }
    return render(request, 'purchase_bill_details.html', context)
from django.shortcuts import render
from .models import PurchaseHistory

def purchase_list(request):
    purchases = PurchaseHistory.objects.select_related('bill').all()
    return render(request, 'purchase_list.html', {'purchases': purchases})


def purchase_details(request, bill_id):
    bill = get_object_or_404(Bill, pk=bill_id)
    purchase_items = PurchaseHistory.objects.filter(bill=bill)
    return render(request, 'purchase_details.html', {'bill': bill, 'purchase_items': purchase_items})
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST
from .models import PurchaseBill  # Make sure this is your model name

@require_POST
def mark_bill_success(request, bill_id):
    bill = get_object_or_404(Bill1, id=bill_id)
    bill.payment_status = 'success'
    bill.save()
    return redirect('create_purchase')  # Replace with your actual view name that renders the bill list

def edit_purchase(request, bill_id):
    bill = get_object_or_404(Bill, pk=bill_id)
    purchase_items = PurchaseHistory.objects.filter(bill=bill)

    if request.method == 'POST':
        try:
            company_name = request.POST.get('company_name', '').strip()
            bill_date = request.POST.get('bill_date')
            payment_mode = request.POST.get('payment_mode')
            cheque_number = request.POST.get('cheque_number', '') if payment_mode == 'cheque' else ''
            cheque_date = request.POST.get('cheque_date', '') if payment_mode == 'cheque' else None
            medicine_ids = request.POST.getlist('medicine_id[]') # To identify existing items
            medicine_names = request.POST.getlist('medicine_name[]')
            medicine_types = request.POST.getlist('medicine_type[]')
            quantities = request.POST.getlist('quantity[]')
            unit_types = request.POST.getlist('unit_type[]')
            batch_numbers = request.POST.getlist('batch_number[]')
            discounts = request.POST.getlist('discount[]')
            expiry_dates = request.POST.getlist('expiry_date[]')
            mrp_rates = request.POST.getlist('mrp[]')
            purchase_rates = request.POST.getlist('purchase_rate[]')
            new_medicine_names = request.POST.getlist('new_medicine_name[]')
            new_medicine_types = request.POST.getlist('new_medicine_type[]')
            new_quantities = request.POST.getlist('new_quantity[]')
            new_unit_types = request.POST.getlist('new_unit_type[]')
            new_batch_numbers = request.POST.getlist('new_batch_number[]')
            new_discounts = request.POST.getlist('new_discount[]')
            new_expiry_dates = request.POST.getlist('new_expiry_date[]')
            new_mrp_rates = request.POST.getlist('new_mrp[]')
            new_purchase_rates = request.POST.getlist('new_purchase_rate[]')
            remove_items = request.POST.getlist('remove_item[]')

            total_bill_amount = Decimal('0.00')

            # Update Bill information
            bill.bill_date = bill_date
            bill.payment_mode = payment_mode
            bill.cheque_number = cheque_number
            bill.cheque_date = cheque_date
            bill.save()

            # Process existing purchase items
            for i in range(len(medicine_ids)):
                item_id = medicine_ids[i]
                try:
                    purchase_item = PurchaseHistory.objects.get(pk=item_id, bill=bill)
                    qty = int(quantities[i]) if quantities[i] else 0
                    rate = Decimal(purchase_rates[i]) if purchase_rates[i] else Decimal('0.00')
                    discount = Decimal(discounts[i]) / 100 if discounts[i] else Decimal('0.00')
                    mrp = Decimal(mrp_rates[i]) if mrp_rates[i] else Decimal('0.00')
                    expiry = expiry_dates[i] if expiry_dates[i] else None
                    batch = batch_numbers[i] if batch_numbers[i] else ''
                    medicine_type = medicine_types[i]
                    medicine_name = medicine_names[i]
                    unit_type = unit_types[i]
                    amount = qty * rate * (1 - discount)
                    total_bill_amount += amount

                    purchase_item.batch_number = batch
                    purchase_item.medicine_name = medicine_name
                    purchase_item.medicine_type = medicine_type
                    purchase_item.unit_type = unit_type
                    purchase_item.qty_in_strip = qty
                    purchase_item.company_name = company_name
                    purchase_item.expiry_date = expiry
                    purchase_item.mrp_rate = mrp
                    purchase_item.shop_rate = rate
                    purchase_item.total_amount = amount
                    purchase_item.save()

                    # Update MedicineMaster (similar logic as create_purchase)
                    medicine_master, created = MedicineMaster.objects.get_or_create(
                        medicine_name=medicine_name,
                        medicine_type=medicine_type,
                        company_name=company_name,
                        defaults={
                            'Number_of_medicines_per_strip': 1,
                            'qty_in_strip': qty,
                            'expiry_date': expiry,
                            'mrp_rate': mrp,
                            'shop_rate': rate,
                            'total_amount': amount,
                        }
                    )
                    if not created:
                        medicine_master.qty_in_strip += qty
                        medicine_master.total_amount += amount
                        medicine_master.expiry_date = max(medicine_master.expiry_date, expiry)
                        medicine_master.shop_rate = (medicine_master.shop_rate * (medicine_master.qty_in_strip - qty) + rate * qty) / medicine_master.qty_in_strip
                        medicine_master.mrp_rate = max(medicine_master.mrp_rate, mrp)
                        medicine_master.save()

                except PurchaseHistory.DoesNotExist:
                    messages.error(request, f"Could not find purchase item with ID {item_id}")
                    return redirect('edit_purchase', bill_id=bill_id)
                except (ValueError, InvalidOperation) as ve:
                    messages.error(request, f"Invalid input in existing medicine entry {i+1}: {ve}")
                    return redirect('edit_purchase', bill_id=bill_id)
                except Exception as e:
                    messages.error(request, f"Error processing existing medicine entry {i+1}: {e}")
                    return redirect('edit_purchase', bill_id=bill_id)

            # Process new purchase items
            for i in range(len(new_medicine_names)):
                if new_medicine_names[i]: # Only process if medicine name is provided
                    try:
                        qty = int(new_quantities[i]) if new_quantities[i] else 0
                        rate = Decimal(new_purchase_rates[i]) if new_purchase_rates[i] else Decimal('0.00')
                        discount = Decimal(new_discounts[i]) / 100 if new_discounts[i] else Decimal('0.00')
                        mrp = Decimal(new_mrp_rates[i]) if new_mrp_rates[i] else Decimal('0.00')
                        expiry = new_expiry_dates[i] if new_expiry_dates[i] else None
                        batch = new_batch_numbers[i] if new_batch_numbers[i] else ''
                        medicine_type = new_medicine_types[i]
                        medicine_name = new_medicine_names[i]
                        unit_type = new_unit_types[i]
                        amount = qty * rate * (1 - discount)
                        total_bill_amount += amount

                        PurchaseHistory.objects.create(
                            bill=bill,
                            batch_number=batch,
                            medicine_name=medicine_name,
                            medicine_type=medicine_type,
                            unit_type=unit_type,
                            qty_in_strip=qty,
                            company_name=company_name,
                            expiry_date=expiry,
                            mrp_rate=mrp,
                            shop_rate=rate,
                            total_amount=amount
                        )

                        # Update MedicineMaster for new items
                        medicine_master, created = MedicineMaster.objects.get_or_create(
                            medicine_name=medicine_name,
                            medicine_type=medicine_type,
                            company_name=company_name,
                            defaults={
                                'Number_of_medicines_per_strip': 1,
                                'qty_in_strip': qty,
                                'expiry_date': expiry,
                                'mrp_rate': mrp,
                                'shop_rate': rate,
                                'total_amount': amount,
                            }
                        )
                        if not created:
                            medicine_master.qty_in_strip += qty
                            medicine_master.total_amount += amount
                            medicine_master.expiry_date = max(medicine_master.expiry_date, expiry)
                            medicine_master.shop_rate = (medicine_master.shop_rate * (medicine_master.qty_in_strip - qty) + rate * qty) / medicine_master.qty_in_strip
                            medicine_master.mrp_rate = max(medicine_master.mrp_rate, mrp)
                            medicine_master.save()

                    except (ValueError, InvalidOperation) as ve:
                        messages.error(request, f"Invalid input in new medicine entry {i+1}: {ve}")
                        return redirect('edit_purchase', bill_id=bill_id)
                    except Exception as e:
                        messages.error(request, f"Error processing new medicine entry {i+1}: {e}")
                        return redirect('edit_purchase', bill_id=bill_id)

            # Remove selected items
            if remove_items:
                PurchaseHistory.objects.filter(id__in=remove_items, bill=bill).delete()

            # Recalculate total bill amount
            bill.bill_amount = PurchaseHistory.objects.filter(bill=bill).aggregate(models.Sum('total_amount'))['total_amount__sum'] or Decimal('0.00')
            bill.save()

            messages.success(request, "Purchase record successfully updated!")
            return redirect('purchase_details', bill_id=bill.id)

        except Exception as e:
            messages.error(request, f"Error occurred during update: {e}")
            return redirect('edit_purchase', bill_id=bill_id)

    context = {
        'bill': bill,
        'purchase_items': purchase_items,
    }
    return render(request, 'purchase_edit_form.html', context)

def delete_purchase(request, bill_id):
    bill = get_object_or_404(Bill, pk=bill_id)
    if request.method == 'POST':
        bill.delete()
        messages.success(request, f"Purchase Bill #{bill.bill_number} has been successfully deleted.")
        return redirect('purchase_list')
    return render(request, 'purchase_confirm_delete.html', {'bill': bill})

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import PurchaseHistory  # Make sure to import the correct model


from .models import PurchaseHistory, MedicineMaster

def get_medicine_details(request):
    if request.method == "POST":
        med_id = request.POST.get("medicine_id")  # Format: "Crocin|B1|123"

        if not med_id or '|' not in med_id:
            return JsonResponse({"error": "Invalid medicine_id format."}, status=400)

        try:
            medicine_name, batch_number, medid = med_id.split('|')
        except ValueError:
            return JsonResponse({"error": "medicine_id must have 3 parts separated by |"}, status=400)

        # Get latest purchase history record
        medicine = PurchaseHistory.objects.filter(
            medicine_name=medicine_name,
            batch_number=batch_number
        ).order_by('-purchase_date').first()

        if not medicine:
            return JsonResponse({"error": f"No purchase history found for {medicine_name} - Batch {batch_number}."}, status=404)

        try:
            master = MedicineMaster.objects.get(medicine_name=medicine_name)
        except MedicineMaster.DoesNotExist:
            return JsonResponse({"error": f"MedicineMaster not found for {medicine_name}."}, status=404)

        medicine_type = master.medicine_type
        Number_of_medicines_per_strip = master.Number_of_medicines_per_strip or 1
        Discount = master.discount or 0

        # Calculate loose rate for tablets only
        if medicine_type == "tablet" and Number_of_medicines_per_strip > 0:
            rate_loose = float(medicine.mrp_rate) / Number_of_medicines_per_strip
        else:
            rate_loose = 0

        return JsonResponse({
            "rate_per_strip": float(medicine.mrp_rate),
            "rate_per_loose": round(rate_loose, 2),
            "qty_per_strip": medicine.qty_in_strip,
            "discount": float(Discount)
        })

    else:
        return JsonResponse({"error": "Invalid request method."}, status=405)


# from django.shortcuts import render, redirect
# from django.http import JsonResponse
# from .models import PurchaseHistory, SalesRegister
# from django.views.decorators.csrf import csrf_exempt

# def sales_register_view(request):
#     medicines = PurchaseHistory.objects.all()
#     sale_details = None  # Initialize to None, in case there's no sale yet.
#     sales = SalesRegister.objects.all()  # Get all sales for the table

#     if request.method == "POST":
#         customer_name = request.POST.get("customer_name")
#         medicine_id = request.POST.get("medicine")
#         qty_strips = int(request.POST.get("qty_strips") or 0)
#         qty_loose = int(request.POST.get("qty_loose") or 0)
#         discount = float(request.POST.get("discount") or 0)
#         total_amount = float(request.POST.get("total_amount") or 0)

#         medicine = PurchaseHistory.objects.get(id=medicine_id)
#         rate_strip = float(medicine.mrp_rate)
#         rate_loose = rate_strip / medicine.qty_per_strip
#         total = (qty_strips * rate_strip) + (qty_loose * rate_loose) - discount

#         # Save the sale in the SalesRegister
#         sale = SalesRegister.objects.create(
#             customer_name=customer_name,
#             medicine=medicine,
#             qty_in_strips=qty_strips,
#             qty_in_loose=qty_loose,
#             discount=discount,
#             total_amount=total_amount
#         )
     
#         medicine_master = MedicineMaster.objects.get(medicine_name=medicine.medicine_name)

        
#         total_available_units = medicine_master.qty_in_strip  

#         total_number_of_medicines=total_available_units * medicine_master.Number_of_medicines_per_strip
#         if qty_strips :
#             if  medicine_master.qty_in_strip :
#                 medicine_master.qty_in_strip=medicine_master.qty_in_strip - qty_strips
#             else:
#                 medicine_master.free_medicine_qty -= qty_strips
     
#             if qty_loose :
#                 medicine_master.loose_medicine += qty_loose
#                 r=medicine_master.loose_medicine / medicine_master.Number_of_medicines_per_strip
#                 print(r)
#                 if  medicine_master.qty_in_strip :
#                     if r < 1:
#                         medicine_master.qty_in_strip -= r
#                     else:
#                         medicine_master.qty_in_strip -= r
#                 else:
#                     if r < 1:
#                         medicine_master.free_medicine_qty -= r
#                     else:
#                         medicine_master.free_medicine_qty -= r
            
#             else :
#                 medicine_master.loose_medicine=total_number_of_medicines-qty_loose
              
#         medicine_master.save()

#         sale_details = {
#             "customer_name": sale.customer_name,
#             "medicine": sale.medicine.medicine_name,
#             "qty_strips": sale.qty_strips,
#             "qty_loose": sale.qty_loose,
#             "discount": sale.discount,
#             "total_amount": sale.total_amount,
#         }

#     return render(request, "sales_register.html", {"medicines": medicines, "sale_details": sale_details, "sales": sales})

# @csrf_exempt
# def get_medicine_details(request):
#     if request.method == "POST":
#         med_id = request.POST.get("medicine_id")
#         medicine = PurchaseHistory.objects.get(id=med_id)
#         rate_loose = float(medicine.mrp_rate) / medicine.Number_of_medicines_per_strip
#         return JsonResponse({
#             "rate_per_strip": float(medicine.mrp_rate),
#             "rate_per_loose": round(rate_loose, 2),
#             "qty_per_strip": medicine.qty_in_strip
#         })

from django.shortcuts import render
from .models import MedicineMaster
from decimal import Decimal
from django.db.models import Sum

def view_medicine_details(request):
    # Fetch all medicine details
    medicines = MedicineMaster.objects.all()

    # Calculate total amount and total medicines for each medicine
    for med in medicines:
        
    
        pack_qty = med.Number_of_medicines_per_strip or 0
       

        # Calculate total amount and total medicines
       


   
        

        result = PurchaseHistory.objects.filter(medicine_name__iexact=med).aggregate(total=Sum('qty_in_strip'))

     
                
        vendors = Vendor.objects.all()
  

    # Pass medicine details to the template
    return render(request, 'medicine_details.html', {'medicines': medicines,'vendors':vendors})

# from django.shortcuts import render, redirect
# from django.http import JsonResponse
# from .models import PurchaseHistory, SalesRegister, MedicineMaster
# from django.contrib import messages
# from django.views.decorators.csrf import csrf_exempt

# def sales_register_view(request):
#     medicines = PurchaseHistory.objects.all()
#     sale_details = None  # Initialize to None, in case there's no sale yet.
#     sales = SalesRegister.objects.all()  # Get all sales for the table

#     if request.method == "POST":
#         customer_name = request.POST.get("customer_name")
#         medicine_id = request.POST.get("medicine")
#         qty_strips = int(request.POST.get("qty_strips") or 0)
#         qty_loose = int(request.POST.get("qty_loose") or 0)
#         discount = float(request.POST.get("discount") or 0)

#         # Fetch the medicine from PurchaseHistory
#         medicine = PurchaseHistory.objects.get(id=medicine_id)
        
#         # Fetch the corresponding medicine from the MedicineMaster table
#         medicine_master = MedicineMaster.objects.get(medicine_name=medicine.medicine_name)  # Assuming there's a foreign key from PurchaseHistory to MedicineMaster

#         rate_strip = float(medicine.mrp_rate)
#         rate_loose = rate_strip / medicine.qty_per_strip
#         total = (qty_strips * rate_strip) + (qty_loose * rate_loose) - discount

#         # Calculate the new available quantities of the medicine
#         new_pack_quantity = medicine.pack_quantity - qty_strips
#         total_medicines_in_stock = (medicine.pack_quantity * medicine.qty_per_strip) + medicine.free_medicine_qty

#         new_loose_quantity = total_medicines_in_stock - (qty_strips * medicine.qty_per_strip) - qty_loose

#         # Check if the medicine has enough stock in PurchaseHistory
#         if new_loose_quantity < 0 or new_pack_quantity < 0:
#             messages.error(request, "Not enough stock available in the Purchase History!")
#             return redirect('sales_register')  # Redirect back if stock is insufficient

#         # Update the medicine stock in the PurchaseHistory
#         medicine.pack_quantity = new_pack_quantity
       
#         medicine.save()  # Save the updated stock in the PurchaseHistory table

#         # Now, update the stock in the MedicineMaster table
#         new_master_pack_quantity = medicine_master.pack_quantity - qty_strips
#         new_master_loose_quantity = total_medicines_in_stock - (qty_strips * medicine_master.qty_per_strip) - qty_loose

#         # Check if there's enough stock in the MedicineMaster table
#         if new_master_loose_quantity < 0 or new_master_pack_quantity < 0:
#             messages.error(request, "Not enough stock available in the Medicine Master!")
#             return redirect('sales_register')  # Redirect if stock is insufficient in the master

#         # Update the stock in the MedicineMaster table
#         medicine_master.pack_quantity = new_master_pack_quantity
     
#         medicine_master.save()  # Save the updated stock in the MedicineMaster table

#         # Save the sale in the SalesRegister
#         sale = SalesRegister.objects.create(
#             customer_name=customer_name,
#             medicine=medicine,
#             qty_strips=qty_strips,
#             qty_loose=qty_loose,
#             discount=discount,
#             total_amount=round(total, 2),
#         )

#         # Prepare the sale details to show the bill on the page
#         sale_details = {
#             "customer_name": sale.customer_name,
#             "medicine": sale.medicine.medicine_name,
#             "qty_strips": sale.qty_strips,
#             "qty_loose": sale.qty_loose,
#             "discount": sale.discount,
#             "total_amount": sale.total_amount,
#         }

#     return render(request, "sales_register.html", {"medicines": medicines, "sale_details": sale_details, "sales": sales})

# @csrf_exempt
# def get_medicine_details(request):
#     if request.method == "POST":
#         med_id = request.POST.get("medicine_id")
#         medicine = PurchaseHistory.objects.get(id=med_id)
#         rate_loose = float(medicine.mrp_rate) / medicine.Number_of_medicines_per_strip
#         return JsonResponse({
#             "rate_per_strip": float(medicine.mrp_rate),
#             "rate_per_loose": round(rate_loose, 2),
#             "qty_per_strip": medicine.qty_in_strip
#         })



from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from .models import PurchaseHistory, SalesRegister, MedicineMaster
from datetime import datetime
from django.db import transaction
from django.http import JsonResponse
from django.db import transaction
from django.db.models import Max
from decimal import Decimal
@csrf_exempt
def sales_register_view(request):
    medicines = PurchaseHistory.objects.values(
    'medicine_name', 'batch_number'
    ).distinct()

    sale_details = None
    sales = SalesRegister.objects.all()
    today_str = date.today().strftime('%Y%m%d')
    latest_bill = SalesRegister.objects.filter(bill_number__startswith=f"BILL{today_str}-").aggregate(Max('bill_number'))['bill_number__max']

    if latest_bill:
        try:
            last_number_str = latest_bill.split('-')[1]
            next_number = int(last_number_str) + 1
            bill_number2 = f"BILL{today_str}-{str(next_number).zfill(4)}"
        except (IndexError, ValueError):
            bill_number2 = f"BILL{today_str}-0001"
    else:
         bill_number2 = f"BILL{today_str}-0001"
 

   


    if request.method == "POST":
        customer_name = request.POST.get("customer_name")

        try:
            with transaction.atomic():
                i = 0
                bill_number1 = request.POST.get("bill_number")

                while True:
                    med_key = f"medicines[{i}][medicine]"
                    if med_key not in request.POST:
                        break

                    medicine_value = request.POST.get(med_key)
                    if not medicine_value:
                        break

                    try:
                        med_name, batch_number, medicine_id = medicine_value.split('|')
                    except ValueError:
                        return JsonResponse({"error": f"Invalid medicine format at entry {i}."}, status=400)

                    try:
                        qty_strips = int(request.POST.get(f"medicines[{i}][qty_strips]") or 0)
                        qty_loose = int(request.POST.get(f"medicines[{i}][qty_loose]") or 0)
                        discount = float(request.POST.get(f"medicines[{i}][discount]") or 0)
                        total_amount_raw = request.POST.get("total_amount", "0")
                    except (TypeError, ValueError):
                        return JsonResponse({"error": f"Invalid quantity or discount at entry {i}."}, status=400)

                    try:
                        medicine_master = MedicineMaster.objects.get(medicine_name=med_name)
                    except MedicineMaster.DoesNotExist:
                        return JsonResponse({"error": f"MedicineMaster not found for {med_name}."}, status=400)
                    
                    if medicine_master.medicine_type == 'tablet':
                        units_per_strip = Decimal(str(medicine_master.Number_of_medicines_per_strip))
                        qty_strips = Decimal(str(qty_strips))
                        qty_loose = Decimal(str(qty_loose))
                        # Calculate total units to sell = strips * units_per_strip + loose units
                        loose_units_to_sell = qty_strips * units_per_strip + qty_loose
                    else:
                        # For liquids/capsules, qty_strips means total quantity
                        loose_units_to_sell = Decimal(str(qty_strips))

                    purchases = PurchaseHistory.objects.filter(
                        medicine_name=med_name,
                        batch_number=batch_number
                    ).order_by('purchase_date')

                    if not purchases.exists():
                        return JsonResponse({"error": f"No purchase history found for {med_name} (Batch {batch_number})."}, status=400)

                    # Check total availability in units
                    total_available = 0
                    for p in purchases:
                        if medicine_master.medicine_type == 'tablet':
                            total_available += p.qty_in_strip * units_per_strip
                        else:
                            total_available += p.qty_in_strip

                    if loose_units_to_sell > total_available:
                        return JsonResponse({"error": f"Insufficient stock for {med_name} (Batch {batch_number})."}, status=400)

                    qty_in_strips_sold = 0
                    qty_in_loose_sold = 0

                    for medicine in purchases:
                        if loose_units_to_sell <= 0:
                            break  # Done selling

                        if medicine_master.medicine_type == 'tablet':
                            units_available = medicine.qty_in_strip * units_per_strip
                            if units_available <= 0:
                                continue

                            deduct_units = min(loose_units_to_sell, units_available)
                            loose_units_to_sell -= deduct_units

                            # Calculate remaining units and update qty_in_strip accordingly
                            remaining_units = units_available - deduct_units
                            medicine.qty_in_strip = remaining_units / units_per_strip

                            medicine.save()

                            qty_in_strips_sold += deduct_units // units_per_strip
                            qty_in_loose_sold += deduct_units % units_per_strip

                        else:
                            units_available = medicine.qty_in_strip
                            if units_available <= 0:
                                continue

                            deduct_units = min(loose_units_to_sell, units_available)
                            loose_units_to_sell -= deduct_units

                            medicine.qty_in_strip = max(0, units_available - deduct_units)
                            medicine.save()

                            qty_in_strips_sold += int(deduct_units)

                    # Create sales entry
                    SalesRegister.objects.create(
                        customer_name=customer_name,
                        bill_number=bill_number1,
                        medicine=medicine,  # last batch used
                        qty_in_strips=qty_strips,
                        qty_in_loose=qty_loose if medicine_master.medicine_type == 'tablet' else 0,
                        discount=discount,
                        total_amount=total_amount_raw
                    )

                    i += 1

                    return redirect('sales_register_view')


            #         if medicine_master.medicine_type == 'tablet':
            #             units_per_strip = Decimal(str(medicine_master.Number_of_medicines_per_strip))
            #             qty_strips = Decimal(str(qty_strips))
            #             qty_loose = Decimal(str(qty_loose))
            #             loose_units_to_sell =  qty_loose
            #         else:
            #             loose_units_to_sell = Decimal(str(qty_strips))  # for liquids/capsules etc.

            #         purchases = PurchaseHistory.objects.filter(
            #             medicine_name=med_name,
            #             batch_number=batch_number
            #         ).order_by('purchase_date')  # use oldest stock first

            #         if not purchases.exists():
            #             return JsonResponse({"error": f"No purchase history found for {med_name} (Batch {batch_number})."}, status=400)

            #         # Check total availability
            #         total_available = 0
            #         for p in purchases:
            #             if medicine_master.medicine_type == 'tablet':
            #                 total_available += p.qty_in_strip * medicine_master.Number_of_medicines_per_strip
            #             else:
            #                 total_available += p.qty_in_strip

            #         if loose_units_to_sell > total_available:
            #             return JsonResponse({"error": f"Insufficient stock for {med_name} (Batch {batch_number})."}, status=400)

            #         qty_in_strips_sold = 0
            #         qty_in_loose_sold = 0

            #         for medicine in purchases:
            #             if loose_units_to_sell <= 0:
            #                 break  # Done selling

            #             if medicine_master.medicine_type == 'tablet':
            #                 units_per_strip = medicine_master.Number_of_medicines_per_strip
            #                 units_available_paid = medicine.qty_in_strip * units_per_strip

            #                 if units_available_paid <= 0:
            #                     continue

            #                 deduct_units = min(loose_units_to_sell, units_available_paid)
            #                 loose_units_to_sell -= deduct_units

            #                 remaining_units = units_available_paid - deduct_units
            #                 updated_qty_in_strip = remaining_units // units_per_strip
            #                 loose_units_remaining = remaining_units % units_per_strip

                           

            #                 # Step 4: Save stock update
            #                 medicine.qty_in_strip = remaining_units/medicine_master.Number_of_medicines_per_strip
            #                 if qty_strips:
            #                     medicine.qty_in_strip -= qty_strips

            #                 # Save updated qty
                  
            #                 medicine.save()

            #                 qty_in_strips_sold += deduct_units // units_per_strip
            #                 qty_in_loose_sold += deduct_units % units_per_strip

            #             else:
            #                 units_available = medicine.qty_in_strip
            #                 if units_available <= 0:
            #                     continue

            #                 deduct_units = min(loose_units_to_sell, units_available)
            #                 loose_units_to_sell -= deduct_units

            #                 medicine.qty_in_strip = max(0, units_available - deduct_units)
            #                 medicine.save()

            #                 qty_in_strips_sold += int(deduct_units)

            #         # Create sales entry (common for both types)
            #         SalesRegister.objects.create(
            #             customer_name=customer_name,
            #             bill_number=bill_number1,
            #             medicine=medicine,  # last batch used
            #             qty_in_strips=qty_strips,
            #             qty_in_loose=qty_in_loose_sold if medicine_master.medicine_type == 'tablet' else 0,
            #             discount=discount,
            #             total_amount=total_amount_raw
            #         )

            #         i += 1

            # return redirect('sales_register_view')


    # if request.method == "POST":
    #     customer_name = request.POST.get("customer_name")

    #     try:
    #         with transaction.atomic():
    #             i = 0
    #             bill_number1 = request.POST.get("bill_number")

    #             while True:
    #                 med_key = f"medicines[{i}][medicine]"
    #                 if med_key not in request.POST:
    #                     break

    #                 medicine_value = request.POST.get(med_key)
    #                 if not medicine_value:
    #                     break

    #                 try:
    #                     med_name, batch_number, medicine_id = medicine_value.split('|')
    #                 except ValueError:
    #                     return JsonResponse({"error": f"Invalid medicine format at entry {i}."}, status=400)

    #                 try:
    #                     qty_strips = int(request.POST.get(f"medicines[{i}][qty_strips]") or 0)
    #                     qty_loose = int(request.POST.get(f"medicines[{i}][qty_loose]") or 0)
    #                     discount = float(request.POST.get(f"medicines[{i}][discount]") or 0)
    #                     total_amount_raw = request.POST.get("total_amount", "0")

    #                 except (TypeError, ValueError):
    #                     return JsonResponse({"error": f"Invalid quantity or discount at entry {i}."}, status=400)

    #                 try:
    #                     medicine_master = MedicineMaster.objects.get(medicine_name=med_name)
    #                 except MedicineMaster.DoesNotExist:
    #                     return JsonResponse({"error": f"MedicineMaster not found for {med_name}."}, status=400)

    #                 if medicine_master.medicine_type == 'tablet':
    #                     units_per_strip = Decimal(str(medicine_master.Number_of_medicines_per_strip))
    #                     qty_strips = Decimal(str(qty_strips))
    #                     qty_loose = Decimal(str(qty_loose))
    #                     loose_units_to_sell =  (qty_loose)
                        
    #                 else:
    #                     loose_units_to_sell = qty_strips  # for liquids/capsules etc.
                    

    #                 # Fetch all batches by latest purchase
    #                 purchases = PurchaseHistory.objects.filter(
    #                     medicine_name=med_name,
    #                     batch_number=batch_number
    #                 ).order_by('-purchase_date')

    #                 if not purchases.exists():
    #                     return JsonResponse({"error": f"No purchase history found for {med_name} (Batch {batch_number})."}, status=400)

    #                 # Check total availability
    #                 total_available = 0
    #                 for p in purchases:
    #                     if medicine_master.medicine_type == 'tablet':
    #                         total_available += (
    #                             (p.qty_in_strip * medicine_master.Number_of_medicines_per_strip)  
    #                         )
    #                     else:
    #                         total_available += p.qty_in_strip 
                    

    #                 if loose_units_to_sell > total_available:
    #                     return JsonResponse({"error": f"Insufficient stock for {med_name} (Batch {batch_number})."}, status=400)

    #                 # Deduct across batches
    #                 for medicine in purchases:
                      

    #                     if medicine_master.medicine_type == 'tablet':
    #                         units_per_strip = medicine_master.Number_of_medicines_per_strip
    #                         units_available_paid = (medicine.qty_in_strip * units_per_strip)

                           

    #                         if units_available_paid <= 0:
    #                             print("No available units. Skipping...")
    #                             continue

    #                         # Step 1: Determine how much to deduct
    #                         deduct_units = min(loose_units_to_sell, units_available_paid)
                           

    #                         # Step 2: Subtract from user’s total required
    #                         loose_units_to_sell -= deduct_units
                          
    #                         # Step 3: Calculate remaining units and update qty_in_strip and loose_units_remaining
    #                         remaining_units = units_available_paid - deduct_units
    #                         updated_qty_in_strip = remaining_units // units_per_strip
    #                         loose_units_remaining = remaining_units % units_per_strip

                           

    #                         # Step 4: Save stock update
    #                         medicine.qty_in_strip = remaining_units/medicine_master.Number_of_medicines_per_strip
    #                         if qty_strips:
    #                             medicine.qty_in_strip -= qty_strips

                        
    #                         medicine.save()
                           
                            
    #                         print("Sales entry recorded successfully.")



    #                     else:
                      
                            
    #                         medicine.qty_in_strip -= qty_strips
                      
    #                         medicine.save()

                          

                            
    #                 if medicine_master.medicine_type == 'tablet':
    #                     SalesRegister.objects.create(
    #                                 customer_name=customer_name,
    #                                 bill_number=bill_number1,
    #                                 medicine=medicine,
    #                                 qty_in_strips=qty_strips,
    #                                 qty_in_loose=qty_loose,
    #                                 discount=discount,
    #                                 total_amount=total_amount_raw
    #                     )
    #                 else:
    #                     SalesRegister.objects.create(
    #                             customer_name=customer_name,
    #                             bill_number=bill_number1,
    #                             medicine=medicine,
    #                             qty_in_strips=qty_strips,
    #                             qty_in_loose=0,
    #                             discount=discount,
    #                             total_amount=total_amount_raw
    #                         )

    #                 i += 1

    #         return redirect('sales_register_view')

  


        except Exception as e:
            return JsonResponse({"error": f"Unexpected error: {str(e)}"}, status=500)


        sale_details = {
            "customer_name": sale.customer_name,
            "medicine": sale.medicine.medicine_name,
            "qty_strips": sale.qty_in_strips,
            "qty_loose": sale.qty_in_loose,
            "discount": sale.discount,
            "total_amount": sale.total_amount,
          
        }

    # Filter sales by date if provided
    filter_date = request.GET.get('filter_date')
    sales_queryset = SalesRegister.objects.all().select_related('medicine')

    if filter_date:
        try:
            date_obj = datetime.strptime(filter_date, '%Y-%m-%d').date()
            sales_queryset = sales_queryset.filter(sale_date__date=date_obj)
        except ValueError:
            sales_queryset = SalesRegister.objects.none()
    else:
        sales_queryset = sales_queryset.order_by('-sale_date')[:20]

    sales_by_bill = {}
    grand_total_amount = 0

    for sale in sales_queryset:
        if sale.bill_number not in sales_by_bill:
            sales_by_bill[sale.bill_number] = []
        sales_by_bill[sale.bill_number].append(sale)

    # Calculate bill totals and grand total
    for bill_number, sales_in_bill in sales_by_bill.items():
        bill_total = sum(sale.total_amount for sale in sales_in_bill)
        grand_total_amount += bill_total
        for sale in sales_in_bill:
            sale.bill_total_amount = bill_total  # Add bill_total_amount to each sale object


    return render(request, "sales_register.html", {
        "medicines": medicines,
        "sale_details": sale_details,
        "sales": sales,
        "filter_date": filter_date,
        "bill_number":bill_number2,
        "sales_by_bill": sales_by_bill,
        "grand_total_amount": grand_total_amount,
        "filter_date": filter_date,
    
 
    })




# def sales_register_view(request):
#     medicines = PurchaseHistory.objects.all()
#     sale_details = None
#     bill_number = f"BILL{date.today().strftime('%Y%m%d')}-{str(SalesRegister.objects.count() + 1).zfill(4)}"

#     if request.method == "POST":
#         customer_name = request.POST.get("customer_name")

#         try:
#             with transaction.atomic():
#                 i = 0
#                 bill_number = request.POST.get("bill_number")
#                 while True:
#                     med_key = f"medicines[{i}][medicine]"
#                     if med_key not in request.POST:
#                         break  # no more medicine entries

#                     medicine_id = request.POST.get(f"medicines[{i}][medicine]")
#                     qty_strips = int(request.POST.get(f"medicines[{i}][qty_strips]") or 0)
#                     qty_loose = int(request.POST.get(f"medicines[{i}][qty_loose]") or 0)
#                     discount = float(request.POST.get(f"medicines[{i}][discount]") or 0)

#                     # Get medicine from purchase history
#                     try:
#                         medicine = PurchaseHistory.objects.get(id=medicine_id)
#                     except PurchaseHistory.DoesNotExist:
#                         return JsonResponse({"error": f"Medicine ID {medicine_id} not found in purchase history."}, status=400)

#                     # Get pricing
#                     rate_strip = float(medicine.mrp_rate)
#                     rate_loose = rate_strip / medicine.Number_of_medicines_per_strip if medicine.medicine_type == 'tablet' else 0

#                     total = (qty_strips * rate_strip) + (qty_loose * rate_loose)
#                     total_after_discount = total - (total * (discount / 100))

#                     # Save sales record
#                     SalesRegister.objects.create(
#                         customer_name=customer_name,
#                         bill_number=bill_number,
#                         medicine=medicine,
#                         qty_in_strips=qty_strips,
#                         qty_in_loose=qty_loose,
#                         discount=discount,
#                         total_amount=total_after_discount
#                     )

#                     # Update MedicineMaster stock
#                     try:
#                         master = MedicineMaster.objects.get(medicine_name=medicine.medicine_name)
#                     except MedicineMaster.DoesNotExist:
#                         return JsonResponse({"error": f"MedicineMaster entry not found for {medicine.medicine_name}."}, status=400)

#                     if master.medicine_type == 'tablet':
#                         total_units_to_reduce = (qty_strips * master.Number_of_medicines_per_strip) + qty_loose
#                         total_loose_available = (master.qty_in_strip * master.Number_of_medicines_per_strip) + master.loose_medicine

#                         if total_units_to_reduce > total_loose_available:
#                             return JsonResponse({"error": f"Insufficient stock for {master.medicine_name}!"}, status=400)

#                         remaining_loose = total_loose_available - total_units_to_reduce
#                         master.qty_in_strip = remaining_loose // master.Number_of_medicines_per_strip
#                         master.loose_medicine = remaining_loose % master.Number_of_medicines_per_strip
#                     else:
#                         if master.qty_in_strip < qty_strips:
#                             return JsonResponse({"error": f"Insufficient stock for {master.medicine_name}!"}, status=400)
#                         master.qty_in_strip -= qty_strips

#                     master.save()
#                     i += 1  # go to next medicine

#             return redirect('sales_register_view')

#         except Exception as e:
#             return JsonResponse({"error": f"Unexpected error: {str(e)}"}, status=500)

#     # Filter sales by date if provided
#     filter_date = request.GET.get('filter_date')
#     sales_queryset = SalesRegister.objects.all().select_related('medicine')

#     if filter_date:
#         try:
#             date_obj = datetime.strptime(filter_date, '%Y-%m-%d').date()
#             sales_queryset = sales_queryset.filter(sale_date__date=date_obj)
#         except ValueError:
#             sales_queryset = SalesRegister.objects.none()
#     else:
#         sales_queryset = sales_queryset.order_by('-sale_date')[:20]

#     sales_by_bill = {}
#     grand_total_amount = 0

#     for sale in sales_queryset:
#         if sale.bill_number not in sales_by_bill:
#             sales_by_bill[sale.bill_number] = []
#         sales_by_bill[sale.bill_number].append(sale)

#     # Calculate bill totals and grand total
#     for bill_number, sales_in_bill in sales_by_bill.items():
#         bill_total = sum(sale.total_amount for sale in sales_in_bill)
#         grand_total_amount += bill_total
#         for sale in sales_in_bill:
#             sale.bill_total_amount = bill_total  # Add bill_total_amount to each sale object

#     context = {
#         "medicines": medicines,
#         "sale_details": sale_details,
#         "sales_by_bill": sales_by_bill,
#         "grand_total_amount": grand_total_amount,
#         "filter_date": filter_date,
#         "bill_number": bill_number,
#     }
#     return render(request, "sales_register.html", context)
# @csrf_exempt
# def get_medicine_details(request):
#     print("_++++")

#     if request.method == "POST":
#         med_id = request.POST.get("medicine_id")
#         medicine = PurchaseHistory.objects.get(id=med_id)
#         if medicine.medicine_type == 'tablet' :

#             rate_loose = float(medicine.mrp_rate) / medicine.Number_of_medicines_per_strip
#         else:

#             return JsonResponse({
#             "rate_per_strip": float(medicine.mrp_rate),
#             "rate_per_loose": 0,
#             "qty_per_strip": medicine.qty_in_strip,
#             "discount":medicine.discount
#         })
    
#         return JsonResponse({
#             "rate_per_strip": float(medicine.mrp_rate),
#             "rate_per_loose": round(rate_loose, 2),
#             "qty_per_strip": medicine.qty_in_strip,
#             "discount":medicine.discount
#         })
# from django.views.decorators.csrf import csrf_exempt
# from django.http import JsonResponse
# from .models import MedicineMaster
# from django.shortcuts import get_object_or_404

# @csrf_exempt
# def get_medicine_details(request):
#     print("_++++")

#     if request.method == "POST":
#         med_id = request.POST.get("medicine_id")

#         # Use get_object_or_404 to avoid server error on missing object
#         print(med_id,")))")
#         medicine = get_object_or_404(MedicineMaster, medicine_name=med_id)

#         # Default values
#         rate_per_strip = float(medicine.mrp_rate)
#         rate_per_loose = 0.0

#         # Calculate loose medicine rate if type is 'tablet'
#         if medicine.medicine_type == 'tablet' and medicine.Number_of_medicines_per_strip > 0:
#             rate_per_loose = rate_per_strip / medicine.Number_of_medicines_per_strip

#         return JsonResponse({
#             "rate_per_strip": rate_per_strip,
#             "rate_per_loose": round(rate_per_loose, 2),
#             "qty_per_strip": medicine.qty_in_strip,
#             "discount": float(medicine.discount),
#             "is_expired": medicine.is_expired,
#             "total_medicines": medicine.total_medicines
#         })

from django.shortcuts import render, redirect, get_object_or_404
from .models import Bill1, PurchaseHistory, Vendor
from .forms import VendorForm

def add_vendor(request):
    form = VendorForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        vendor = form.save(commit=False)
        vendor.save()
        return redirect('add_vendor')  # Update this URL name to match your project

    vendors = Vendor.objects.all()
    context = {
        'form': form,
        'vendors': vendors,
    }
    return render(request, 'add_vendor.html', context)

from collections import defaultdict
from django.db.models import F
from pprint import pprint
def vendor_bills(request, vendor_id):
    vendor = get_object_or_404(Vendor, id=vendor_id)
    
    # Find bills linked to this vendor via PurchaseHistory
    related_bill_ids = PurchaseHistory.objects.filter(company_name=vendor.name).values_list('bill_id', flat=True).distinct()
    bills = Bill1.objects.filter(id__in=related_bill_ids)

    vendors = Vendor.objects.all()  # Needed to display in the template

    # Get the bill_date from GET params (frontend)
    grouped_bills_clean = []  # default empty list
    bill_date_str = request.GET.get('bill_date')  # e.g., "2025-05-15"
    if bill_date_str:
        try:
            bill_date = datetime.strptime(bill_date_str, '%Y-%m-%d').date()
            bills = bills.filter(bill_date=bill_date)

            grouped_bills = defaultdict(list)
            for bill in bills:
                key = (bill.combined_pay, bill.bill_date)
                grouped_bills[key].append(bill)

            for (combined_pay, bill_date_key), bills_list in grouped_bills.items():
                grouped_bills_clean.append({
                    'combined_pay': combined_pay,
                    'bill_date': bill_date_key,
                    'bills_list': bills_list,
                })
        except ValueError:
            # Invalid date, keep grouped_bills_clean empty
            pass



    return render(request, 'add_vendor.html', {
        'vendors': vendors,
        'selected_vendor': vendor,
        'bills': bills,
        'grouped_bills': grouped_bills_clean,
        'form': VendorForm(),  # Re-add form for UI reuse
    })
# from collections import defaultdict
# from django.db.models import F

# def vendor_bills(request, vendor_id):
#     vendor = get_object_or_404(Vendor, id=vendor_id)

#     # Fetch related bills
#     related_bill_ids = PurchaseHistory.objects.filter(
#         company_name=vendor.name
#     ).values_list('bill_id', flat=True).distinct()

#     bills = Bill1.objects.filter(id__in=related_bill_ids)

#     # Grouping bills by combined_pay and bill_date
#     grouped_bills = defaultdict(list)
#     for bill in bills:
#         key = (bill.combined_pay, bill.bill_date)
#         grouped_bills[key].append(bill)

#     vendors = Vendor.objects.all()

#     return render(request, 'add_vendor.html', {
#         'vendors': vendors,
#         'selected_vendor': vendor,
#         'grouped_bills': grouped_bills,
#         'form': VendorForm(),
#     })




def vendor_success(request):
    return render(request, 'vendor_success.html')
from django.shortcuts import redirect, get_object_or_404
from .models import Bill1
from django.utils import timezone
from django.db import transaction

def bulk_mark_bills_paid(request, vendor_id):
    if request.method == 'POST':
        bill_ids = request.POST.getlist('bill_ids')
        payment_mode = request.POST.get('payment_mode')
        cheque_number = request.POST.get('cheque_number')
        cheque_date = request.POST.get('cheque_date')

        bills = Bill1.objects.filter(id__in=bill_ids)

        # Create combined_pay from bill_numbers
        bill_numbers = [bill.bill_number for bill in bills]
        combined_pay_value = "_".join(bill_numbers)  # e.g., B001_B002

        with transaction.atomic():
            for bill in bills:
                bill.payment_status = 'success'  # you had 'success' which is not in your choices
                bill.bill_date = timezone.now()
                bill.payment_mode = payment_mode
                bill.combined_pay = combined_pay_value  # store same value in all selected bills

                if payment_mode == 'cheque':
                    bill.cheque_number = cheque_number
                    bill.cheque_date = cheque_date
                else:
                    bill.cheque_number = None
                    bill.cheque_date = None

                bill.save()

        return redirect('vendor_bills', vendor_id=vendor_id)

    return redirect('vendor_bills', vendor_id=vendor_id)
from .forms import MedicineMasterForm
# Edit View
def edit_medicine(request, pk):
    medicine = get_object_or_404(MedicineMaster, pk=pk)
    if request.method == 'POST':
        form = MedicineMasterForm(request.POST, instance=medicine)
        if form.is_valid():
            form.save()
            return redirect('view_medicine_details')
    else:
        form = MedicineMasterForm(instance=medicine)
    return render(request, 'edit_medicine.html', {'form': form})

# Delete View
def delete_medicine(request, pk):
    medicine = get_object_or_404(MedicineMaster, pk=pk)
    medicine.delete()
    return redirect('view_medicine_details')
def get_discount(request):
    medicine_id = request.GET.get('medicine_id')

    if not medicine_id:
        return JsonResponse({'error': 'Medicine ID is required'}, status=400)

    try:
        print("if",id)
        purchase = PurchaseHistory.objects.filter(
            id=medicine_id,
            expiry_date__gte=date.today()
        ).order_by('-purchase_date').first()
     

        if purchase and purchase.mrp_rate > 0:
            discount = ((purchase.mrp_rate - purchase.shop_rate) / purchase.mrp_rate) * 100
            return JsonResponse({'discount': round(discount, 2)})
        else:
            return JsonResponse({'discount': 0})
    except PurchaseHistory.DoesNotExist:
        return JsonResponse({'discount': 0})

from django.shortcuts import render
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from .models import SalesRegister

def print_bill_pdf(request, bill_number):
    sales = SalesRegister.objects.filter(bill_number=bill_number)
    if not sales.exists():
        return HttpResponse("No sales found for this bill", status=404)

    total = sum(s.total_amount for s in sales)
    template = get_template("print_bill.html")
    html = template.render({
        'sales': sales,
        'bill_number': bill_number,
        'customer_name': sales[0].customer_name,
        'sale_date': sales[0].sale_date,
        'total': total,
    })

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="Bill_{bill_number}.pdf"'
    pisa_status = pisa.CreatePDF(html, dest=response)
    return response

from django.shortcuts import render, redirect
from .models import MedicineMaster
from datetime import datetime

def add_medicine1(request):
    if request.method == 'POST':
        try:
            medicine_name = request.POST.get('medicine_name')
            medicine_type = request.POST.get('medicine_type')
            number_of_medicines_per_strip = int(request.POST.get('number_of_medicines_per_strip', 0))
            
            
            discount = float(request.POST.get('discount', 0))

            # Save to database
            print("))_)_)")
            MedicineMaster.objects.create(
                medicine_name=medicine_name,
                medicine_type=medicine_type,
                Number_of_medicines_per_strip=number_of_medicines_per_strip,
                discount=discount,
            )
            print(")_)_")
            return redirect('view_medicine_details')
        
        except Exception as e:
            return render(request, 'medicine_details.html', {
                'error': f"Error while saving medicine: {str(e)}"
            })

    medicines = MedicineMaster.objects.all().order_by('medicine_name')
    vendors = Vendor.objects.all()


    return render(request, 'medicine_details.html', {'medicines': medicines,'vendors':vendors})
# views.py
from django.shortcuts import render, get_object_or_404, redirect
from .models import PurchaseHistory
from datetime import date
from django.db.models import Sum
from django.contrib import messages


from django.db.models import Sum, Min

from django.db.models import Sum, Min
from datetime import date

def medicine_list_view(request):
    medicines = (
        PurchaseHistory.objects
        .values('medicine_name', 'batch_number', 'company_name')  # include company_name here
        .annotate(
            total_qty=Sum('qty_in_strip'),
            total_free_qty=Sum('free_medicine_qty'),
            total_amount=Sum('total_amount'),
            earliest_expiry=Min('expiry_date'),
            mrp_rate=Min('mrp_rate'),
            shop_rate=Min('shop_rate'),
        )
        .order_by('medicine_name', 'batch_number')
    )
    return render(request, 'medicine_list.html', {'medicines': medicines, 'today': date.today()})




def edit_medicine_view(request, medicine_name, batch_number):
    medicine = get_object_or_404(PurchaseHistory, medicine_name=medicine_name, batch_number=batch_number)
    if request.method == 'POST':
        medicine.medicine_name = request.POST.get('medicine_name')
        medicine.company_name = request.POST.get('company_name')
        medicine.batch_number = request.POST.get('batch_number')
        medicine.qty_in_strip = request.POST.get('qty_in_strip')
        medicine.free_medicine_qty = request.POST.get('free_medicine_qty')
        medicine.mrp_rate = request.POST.get('mrp_rate')
        medicine.shop_rate = request.POST.get('shop_rate')
        medicine.total_amount = request.POST.get('total_amount')
        medicine.expiry_date = request.POST.get('expiry_date')
        medicine.save()
        messages.success(request, "Medicine details updated successfully.")
        return redirect('medicine_list_view')
    return render(request, 'edit_medicine1.html', {'medicine': medicine})


def delete_medicine_group_view(request, medicine_name, batch_number):
    PurchaseHistory.objects.filter(medicine_name=medicine_name, batch_number=batch_number).delete()
    messages.success(request, f"All records for {medicine_name} (Batch {batch_number}) deleted.")
    return redirect('medicine_list_view')


from django.db.models import Sum

def view_purchases(request, medicine_name, batch_number):
    purchases = PurchaseHistory.objects.filter(
        medicine_name=medicine_name,
        batch_number=batch_number
    )

    total_quantity = purchases.aggregate(total_qty=Sum('qty_in_strip'))['total_qty'] or 0
    total_free_quantity = purchases.aggregate(total_free=Sum('free_medicine_qty'))['total_free'] or 0

    return render(request, 'purchases_view.html', {
        'purchases': purchases,
        'medicine_name': medicine_name,
        'batch_number': batch_number,
        'total_quantity': total_quantity,
        'total_free_quantity': total_free_quantity,
    })


