# 💊 Pharmacy Management System

A full-featured web-based Pharmacy Management System designed to automate and manage medicine inventory, sales, billing, and customer records. The application provides user-friendly interfaces, admin and pharmacist roles, and essential reports for daily operations.

---

## 🔧 Tech Stack

- **Backend:** Python, Django  
- **Frontend:** HTML, CSS, Bootstrap, JavaScript  
- **Database:** MySQL / SQLite  
- **Authentication:** Django Auth  
- **Others:** jQuery, AJAX (if used), PDF Generation (optional)

---

## ✅ Features

- 📦 **Inventory Management** — Add, update, and remove medicines.  
- 📋 **Sales Management** — Generate bills and track sales transactions.  
- 👤 **Customer & Supplier Management** — Manage customer and supplier info.  
- 🗓️ **Expiry Alerts** — Notify low stock and near-expiry medicines.  
- 📊 **Reports Dashboard** — Visual and tabular sales/purchase reports.  
- 🔐 **User Roles** — Admin and pharmacist access levels.  
- 🧾 **Invoice Generation** — Printable invoice generation with medicine details.  

---

## 📁 Project Structure

```bash
pharmacy-management/
├── manage.py
├── env/                   # Virtual environment (not pushed to Git)
├── requirements.txt
├── pharmacy_app/
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── views.py
│   ├── forms.py
│   ├── urls.py
│   ├── templates/
│   └── static/
└── db.sqlite3             # or your MySQL connection
