from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import UserEditForm
from .forms import BudgetForm
from .decorators import login_required  # Import the custom decorator
from .forms import ProfilePhotoForm, UsernameForm, UserPasswordChangeForm
from .models import Transaction
from django.http import JsonResponse
from .models import UserAccount, Transaction
from datetime import datetime
from decimal import Decimal
from .forms import BudgetLimitForm
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect
from .forms import TransactionForm
import csv
from io import BytesIO
from openpyxl import Workbook
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from django.http import HttpResponse
import xlsxwriter
import csv
from io import BytesIO
from openpyxl import Workbook
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

def calculate_balance(user_account):
    return user_account.soldePris - user_account.soldeDepense

@login_required
def transaction_detail(request, transaction_id):
    transaction = get_object_or_404(Transaction, id=transaction_id, user=request.user)

    if request.method == 'POST':
        original_amount = transaction.amount
        original_transaction_type = transaction.transaction_type
        
        # Delete the transaction
        transaction.delete()

        # Update the user account balances based on the deleted transaction
        user_account = UserAccount.objects.get(user=request.user)
        if original_transaction_type == 'PRIS':
            user_account.soldePris -= original_amount
            user_account.soldePris = max(user_account.soldePris, 0)
        else:
            user_account.soldeDepense += original_amount

        user_account.save()

        return redirect('home')

    return render(request, 'pages/transaction_detail.html', {
        'transaction': transaction,
    })
@login_required
def transaction_modify(request, transaction_id):
    transaction = get_object_or_404(Transaction, id=transaction_id, user=request.user)
    original_transaction_type = transaction.transaction_type
    original_amount = transaction.amount

    if request.method == 'POST':
        form = TransactionForm(request.POST, instance=transaction)
        if form.is_valid():
            updated_transaction = form.save(commit=False)
            updated_amount = updated_transaction.amount
            updated_transaction.save()

            # Update the user account balances based on the changes in the transaction
            user_account = UserAccount.objects.get(user=request.user)

            # Revert the original transaction's impact on balances
            if original_transaction_type == 'PRIS':
                user_account.soldePris -= original_amount
            else:
                user_account.soldeDepense += original_amount

            # Apply the updated transaction's impact on balances
            if updated_transaction.transaction_type == 'PRIS':
                user_account.soldePris += updated_amount
            else:
                user_account.soldeDepense -= updated_amount

            # Recalculate the balance
            user_account.balance = calculate_balance(user_account)

            user_account.save()

            return redirect('transaction_detail', transaction_id=transaction.id)
    else:
        form = TransactionForm(instance=transaction)

    return render(request, 'pages/transaction_modify.html', {
        'transaction': transaction,
        'form': form,
    })
@login_required
def home(request):
    try:
        # Attempt to retrieve the UserAccount associated with the current user
        user_account = UserAccount.objects.get(user=request.user)
    except UserAccount.DoesNotExist:
        # If UserAccount does not exist, create it
        user_account = UserAccount.objects.create(user=request.user)
        # You might want to add more fields to the UserAccount upon creation
        
    if 'activate_budget_limit' in request.POST:
            user_account = UserAccount.objects.get(user=request.user)
            user_account.budget_limit_active = True
            user_account.save()
            return redirect('home')
    elif 'deactivate_budget_limit' in request.POST:
            user_account = UserAccount.objects.get(user=request.user)
            user_account.budget_limit_active = False
            user_account.save()
            return redirect('home')
    # Retrieve transaction information
    transactions = Transaction.objects.filter(user=request.user)  # Assuming transactions are related to the logged-in user
    
     # Retrieve transaction information
    transactions = Transaction.objects.filter(user=request.user).order_by('-date')
    
    # Paginate transactions
    paginator = Paginator(transactions, 10)  # Show 10 transactions per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    # Calculate balance and solde based on transactions
    balance = calculate_balance(user_account)
    solde_pris = +user_account.soldePris
    solde_depense = -user_account.soldeDepense 
    budget = user_account.budget
     
    rest_budget = user_account.budget + solde_depense
    budget_limit_active = user_account.budget_limit_active
    context = {
        'balance': balance,
        'solde_pris': solde_pris,
        'solde_depense': solde_depense,
        'user_photo': user_account.photo.url if user_account.photo else None,
        'budget': budget,
        'page_obj': page_obj,
        'rest': rest_budget,
        'solde_depense_abs': abs(solde_depense),
        'budget_limit_active': budget_limit_active,
    }

    return render(request, 'index.html', context)
@login_required
def rapport(request):
    user_account = UserAccount.objects.get(user=request.user)
    transactions = Transaction.objects.filter(user=request.user)

    solde_pris = user_account.soldePris
    solde_depense = user_account.soldeDepense
    balance = calculate_balance(user_account)

    context = {
        'balance': balance,
        'solde_pris': solde_pris,
        'solde_depense': solde_depense,
        'user_photo': user_account.photo.url if user_account.photo else None,
        'budget': user_account.budget,
        'transaction_count': transactions.count(),
    }

    # Check if the request is for downloading a report
    if 'download' in request.GET:
        format = request.GET.get('format')
        if format == 'csv':
            return download_csv(transactions)
        elif format == 'excel':
            return download_excel(transactions)
        elif format == 'pdf':
            return download_pdf(transactions, context)
    
    return render(request, 'pages/rapport.html', context)

@login_required
def download_report(request, file_format):
    user_account = UserAccount.objects.get(user=request.user)
    transactions = Transaction.objects.filter(user=request.user)
    
    if file_format == 'csv':
        return download_csv(transactions)
    elif file_format == 'xlsx':
        return download_xlsx(transactions)
    elif file_format == 'pdf':
        return download_pdf(transactions)
    else:
        messages.error(request, 'Invalid file format.')
        return redirect('rapport')

def download_csv(transactions):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="rapport.csv"'

    writer = csv.writer(response)
    writer.writerow(['Title', 'Amount', 'Category', 'Details', 'Date'])

    for transaction in transactions:
        writer.writerow([transaction.title, transaction.amount, transaction.category, transaction.details, transaction.date])

    return response

def download_xlsx(transactions):
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="rapport.xlsx"'

    workbook = xlsxwriter.Workbook(response, {'in_memory': True})
    worksheet = workbook.add_worksheet()

    # Add headers
    headers = ['Title', 'Amount', 'Category', 'Details', 'Date']
    header_format = workbook.add_format({'bold': True, 'bg_color': '#F9DA04', 'border': 1})
    for col_num, header in enumerate(headers):
        worksheet.write(0, col_num, header, header_format)

    # Add data
    data_format = workbook.add_format({'border': 1})
    for row_num, transaction in enumerate(transactions, start=1):
        worksheet.write(row_num, 0, transaction.title, data_format)
        worksheet.write(row_num, 1, transaction.amount, data_format)
        worksheet.write(row_num, 2, transaction.category, data_format)
        worksheet.write(row_num, 3, transaction.details, data_format)
        worksheet.write(row_num, 4, str(transaction.date), data_format)

    workbook.close()
    return response

def download_pdf(transactions):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="rapport.pdf"'

    pdf = canvas.Canvas(response, pagesize=letter)
    pdf.setTitle('Rapport')

    # Header
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(30, 750, 'Title')
    pdf.drawString(130, 750, 'Amount')
    pdf.drawString(230, 750, 'Category')
    pdf.drawString(330, 750, 'Details')
    pdf.drawString(430, 750, 'Date')

    # Add data
    y = 730
    pdf.setFont("Helvetica", 10)
    for transaction in transactions:
        pdf.drawString(30, y, transaction.title)
        pdf.drawString(130, y, str(transaction.amount))
        pdf.drawString(230, y, transaction.category)
        pdf.drawString(330, y, transaction.details)
        pdf.drawString(430, y, str(transaction.date))
        y -= 20

        if y < 50:  # New page if data exceeds the current page
            pdf.showPage()
            pdf.setFont("Helvetica-Bold", 12)
            pdf.drawString(30, 750, 'Title')
            pdf.drawString(130, 750, 'Amount')
            pdf.drawString(230, 750, 'Category')
            pdf.drawString(330, 750, 'Details')
            pdf.drawString(430, 750, 'Date')
            y = 730

    pdf.save()
    return response

def calculate_balance(user_account):
    return user_account.soldePris - user_account.soldeDepense
@login_required 
def statistiques(request):
     # Retrieve user account information
    user_account = UserAccount.objects.get(user=request.user)  # Assuming user is logged in

    # Retrieve transaction information
    transactions = Transaction.objects.filter(user=request.user)  # Assuming transactions are related to the logged-in user

    # Calculate balance and solde based on transactions
    balance = user_account.balance  # You need to define how balance is calculated based on your application logic
    solde_pris = +user_account.soldePris
    # sum(transaction.amount for transaction in transactions if transaction.amount > 0)
    solde_depense = user_account.soldeDepense
    # sum(transaction.amount for transaction in transactions if transaction.amount < 0)

    context = {
        'solde_pris':solde_pris,
        'solde_depense_abs': abs(solde_depense),
        'balance': balance,
        'solde_pris': solde_pris,
        'solde_depense': solde_depense,
        'user_photo': user_account.photo.url if user_account.photo else None,
    }
    return render(request,'pages/statistiques.html',context)
@login_required
def profile(request):
     # Retrieve user account information
    user_account = UserAccount.objects.get(user=request.user)  # Assuming user is logged in

    # Retrieve transaction information
    transactions = Transaction.objects.filter(user=request.user)  # Assuming transactions are related to the logged-in user

    # Calculate balance and solde based on transactions
    balance = user_account.balance  # You need to define how balance is calculated based on your application logic
    solde_pris = +user_account.soldePris
    # sum(transaction.amount for transaction in transactions if transaction.amount > 0)
    solde_depense = user_account.soldeDepense
    # sum(transaction.amount for transaction in transactions if transaction.amount < 0)

    context = {
        'balance': balance,
        'solde_pris': solde_pris,
        'solde_depense': solde_depense,
        'user_photo': user_account.photo.url if user_account.photo else None,
    }
    user = request.user
    return render(request,'pages/profile.html',{'user': user},context)
@login_required
def profile(request):
    if request.method == 'POST':
        form = UserEditForm(request.POST)
        if form.is_valid():
            user = request.user
            user.first_name = form.cleaned_data['first_name']
            user.last_name = form.cleaned_data['last_name']
            user.email = form.cleaned_data['email']
            user.save()
            return redirect('profile')
    else:
        initial_data = {
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'email': request.user.email,
        }
        form = UserEditForm(initial=initial_data)
    
    # Retrieve user photo from UserAccount model
    user_account = UserAccount.objects.get(user=request.user)
    user_photo = user_account.photo.url if user_account.photo else ''
    
    return render(request, 'pages/profile.html', {'form': form, 'user_photo': user_photo})
@login_required
def settings(request):
    if request.method == 'POST':
        if 'activate_budget_limit' in request.POST:
            user_account = UserAccount.objects.get(user=request.user)
            user_account.budget_limit_active = True
            user_account.save()
            return redirect('settings')
        elif 'deactivate_budget_limit' in request.POST:
            user_account = UserAccount.objects.get(user=request.user)
            user_account.budget_limit_active = False
            user_account.save()
            return redirect('settings')
        elif 'photo' in request.FILES:
            photo_form = ProfilePhotoForm(request.POST, request.FILES)
            if photo_form.is_valid():
                user_account = UserAccount.objects.get(user=request.user)
                user_account.photo = photo_form.cleaned_data['photo']
                user_account.save()
            else:
                messages.error(request, 'Failed to update profile photo.')
        elif 'username' in request.POST:
            username_form = UsernameForm(request.POST, instance=request.user)
            if username_form.is_valid():
                username_form.save()
                
            else:
                messages.error(request, 'Failed to update username.')
        elif 'old_password' in request.POST:
            password_form = UserPasswordChangeForm(user=request.user, data=request.POST)
            if password_form.is_valid():
                password_form.save()
                
            else:
                messages.error(request, 'Failed to update password.')
        elif 'budget' in request.POST:
            budget_form = BudgetForm(request.POST)
            if budget_form.is_valid():
                user_account = UserAccount.objects.get(user=request.user)
                user_account.budget = budget_form.cleaned_data['budget']
                user_account.save()
                
            else:
                messages.error(request, 'Failed to update budget.')
        return redirect('settings')  # Redirect back to settings page after processing form
    else:
                photo_form = ProfilePhotoForm()
                username_form = UsernameForm(instance=request.user)
                password_form = UserPasswordChangeForm(user=request.user)
                budget_form = BudgetForm()
                budget_limit_form = BudgetLimitForm()

    user_account = UserAccount.objects.get(user=request.user)
    user_photo = user_account.photo.url if user_account.photo else ''

    return render(request, 'pages/settings.html', {
        'photo_form': photo_form,
        'username_form': username_form,
        'password_form': password_form,
        'budget_form': budget_form,
        'user_photo': user_photo,
    })


@login_required
def jai_pris(request):
    if request.method == 'POST':
        try:
            amount = Decimal(request.POST['amount'])
        except (ValueError, InvalidOperation):
            messages.error(request, 'Invalid amount. Please enter a valid number.')
            return redirect('jai_pris')
        
        title = request.POST['title']
        category = request.POST['category']
        details = request.POST['details']
        date = request.POST['date']
        
        user_account = UserAccount.objects.get(user=request.user)
        user_account.soldePris += amount
        user_account.balance += amount
        user_account.save()

        Transaction.objects.create(
            user=request.user,
            title=title,
            amount=amount,
            category=category,
            details=details,
            date=datetime.strptime(date, '%Y-%m-%d'),
            transaction_type='PRIS'
        )

        return redirect('home')

    user_account = UserAccount.objects.get(user=request.user)
    user_photo = user_account.photo.url if user_account.photo else None
    return render(request, 'pages/jaiPris.html', {'user_photo': user_photo})

@login_required
def jai_donne(request):
    if request.method == 'POST':
        try:
            amount = Decimal(request.POST['amount'])  # Convert to Decimal
        except (ValueError, InvalidOperation):
            messages.error(request, 'Invalid amount. Please enter a valid number.')
            return redirect('jai_donne')

        title = request.POST['title']
        category = request.POST['category']
        details = request.POST['details']
        date = request.POST['date']
        
        user_account = UserAccount.objects.get(user=request.user)
        new_solde_depense = user_account.soldeDepense + amount
        eta = user_account.budget_limit_active
        if  (new_solde_depense > user_account.budget) and eta:
            messages.error(request, 'La transaction dépasse le budget. Veuillez revoir vos dépenses.')
            return redirect('jai_donne')
        
        user_account.soldeDepense = new_solde_depense
        user_account.balance -= amount
        user_account.save()

        Transaction.objects.create(
            user=request.user,
            title=title,
            amount=-amount,  # Ensure expense amounts are negative
            category=category,
            details=details,
            date=datetime.strptime(date, '%Y-%m-%d'),
            transaction_type='DONNE'
        )
        
        return redirect('home')
    
    
    user_account = UserAccount.objects.get(user=request.user)
    user_photo = user_account.photo.url if user_account.photo else None
    budget_limit_active = user_account.budget_limit_active
    return render(request, 'pages/jaiDonne.html', {'user_photo': user_photo,'budget_limit_active':budget_limit_active})

    if request.method == 'POST':
        try:
            amount = Decimal(request.POST['amount'])  # Convert to Decimal
        except (ValueError, InvalidOperation):
            messages.error(request, 'Invalid amount. Please enter a valid number.')
            return redirect('jai_donne')

        category = request.POST['category']
        details = request.POST['details']
        date = request.POST['date']
        
        user_account = UserAccount.objects.get(user=request.user)
        new_solde_depense = user_account.soldeDepense + amount
        
        if new_solde_depense > user_account.budget:
            messages.error(request, 'Transaction exceeds budget. Please review your expenses.')
            return redirect('jai_donne')
        
        user_account.soldeDepense = new_solde_depense
        user_account.balance -= amount
        user_account.save()

        Transaction.objects.create(
            user=request.user,
            amount=-amount,  # Ensure expense amounts are negative
            category=category,
            details=details,
            date=datetime.strptime(date, '%Y-%m-%d'),
            transaction_type='DONNE'
        )
        
        
        return redirect('home')
    
    user_account = UserAccount.objects.get(user=request.user)
    user_photo = user_account.photo.url if user_account.photo else None
    return render(request, 'pages/jaiDonne.html', {'user_photo': user_photo})

@login_required
def search_transactions(request):
    query = request.GET.get('q', '')
    if query:
        transactions = Transaction.objects.filter(user=request.user, title__icontains=query)
        results = [
            {
                'id': transaction.id,
                'title': transaction.title,
                'amount': transaction.amount,
                'date': transaction.date,
                'description': transaction.details,
            }
            for transaction in transactions
        ]
        print(f"Results: {results}")  # Debug print statement

    else:
        results = []
    return JsonResponse(results, safe=False)
