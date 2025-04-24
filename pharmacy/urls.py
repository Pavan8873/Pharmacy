from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),  # ✅ Add this
    path('', views.dashboard, name='dashboard'),

    path('companies/', views.company_list, name='company_list'),
    path('companies/add/', views.add_company, name='add_company'),
    path('companies/update/<int:pk>/', views.update_company, name='update_company'),
    path('companies/delete/<int:pk>/', views.delete_company, name='delete_company'),


    path('medicines/', views.medicine_list, name='medicine_list'),
    path('medicine/add/', views.add_medicine, name='add_medicine'),
    path('medicines/update/<int:pk>/', views.update_medicine, name='update_medicine'),
    path('medicine/delete/<int:pk>/', views.delete_medicine, name='delete_medicine'),
    # path('purchase_bill/<int:company_id>/', views.generate_purchase_bill, name='generate_purchase_bill'),
    # path('sale_bill/<int:customer_id>/', views.generate_sale_bill, name='generate_sale_bill'),

    path('purchase-bill/', views.generate_purchase_bill, name='generate_purchase_bill'),
    path('get-medicines/', views.get_medicines_by_company, name='get_medicines_by_company'),
    path('sale-bill/', views.generate_sale_bill, name='generate_sale_bill'),
    path('purchase-history/', views.purchase_history, name='purchase_history'),
    path('sales-history/', views.sales_history, name='sales_history'),
    path('create_purchase/', views.create_purchase, name='create_purchase'),
    path('edit_purchase/<int:pk>/', views.edit_purchase, name='edit_purchase'),
    path('delete_purchase/<int:pk>/', views.delete_purchase, name='delete_purchase'),
    path('sales/', views.sales_register_view, name='sales_register_view'),
    path('get-medicine-details/', views.get_medicine_details, name='get-medicine-details'),



]
