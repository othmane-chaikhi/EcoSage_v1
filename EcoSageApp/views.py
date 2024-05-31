from django.shortcuts import render, redirect,get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import UserEditForm,BudgetForm,ProfilePhotoForm, UsernameForm, UserPasswordChangeForm,BudgetLimitForm,TransactionForm
from .decorators import login_required  
from .models import Transaction,UserAccount, Transaction
from datetime import datetime
from decimal import Decimal
from django.core.paginator import Paginator
import csv
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from django.http import HttpResponse
import xlsxwriter
from reportlab.lib.utils import ImageReader



def calculate_balance(user_account):
    return user_account.soldePris - user_account.soldeDepense
@login_required
def transaction_detail(request, transaction_id):
    transaction = get_object_or_404(Transaction, id=transaction_id, user=request.user)

    if request.method == 'POST':
        original_amount = abs(transaction.amount)
        original_transaction_type = transaction.transaction_type
        
        # Delete the transaction
        transaction.delete()

        # Update the user account balances based on the deleted transaction
        user_account = UserAccount.objects.get(user=request.user)
        if original_transaction_type == 'PRIS':
            user_account.soldePris -= original_amount
            user_account.soldePris = max(user_account.soldePris, 0)
        else:
            user_account.soldeDepense -= original_amount

        user_account.save()

        return redirect('home')
    user_account = UserAccount.objects.get(user=request.user)
    return render(request, 'pages/transaction_detail.html', {
        'transaction': transaction,
        'user_photo': user_account.photo.url if user_account.photo else None,
    })
def calculate_balance(user_account):
    return user_account.soldePris - abs(user_account.soldeDepense)

@login_required
def transaction_modify(request, transaction_id):
    transaction = get_object_or_404(Transaction, id=transaction_id, user=request.user)
    original_transaction_type = transaction.transaction_type
    original_amount = transaction.amount
    original_amount_abs = abs(original_amount)

    if request.method == 'POST':
        form = TransactionForm(request.POST, instance=transaction)
        if form.is_valid():
            updated_transaction = form.save(commit=False)
            updated_amount = updated_transaction.amount
            updated_amount_abs = abs(updated_amount)

            user_account = UserAccount.objects.get(user=request.user)
            budget_limit_active = user_account.budget_limit_active
            budget = user_account.budget

           # Annuler l'impact de la transaction d'origine sur les soldes
            if original_transaction_type == 'PRIS':
                user_account.soldePris -= original_amount_abs
            else:
                user_account.soldeDepense -= original_amount_abs

            # Appliquer l'impact de la transaction mise à jour sur les soldes et vérifier le budget
            if updated_transaction.transaction_type == 'PRIS':
                user_account.soldePris += updated_amount_abs
            else:
                new_solde_depense = user_account.soldeDepense + updated_amount_abs
                if budget_limit_active and new_solde_depense > budget:
                    messages.error(request, 'La transaction dépasse le budget. Veuillez revoir vos dépenses.')
                    # Remettre les soldes à l'état d'origine
                    if original_transaction_type == 'PRIS':
                        user_account.soldePris += original_amount_abs
                    else:
                        user_account.soldeDepense += original_amount_abs
                        
                    return redirect('transaction_modify', transaction_id=transaction.id)
                user_account.soldeDepense += updated_amount_abs
                

            # Recalculer la soudure
            user_account.balance = calculate_balance(user_account)
            
            user_account.save()

            updated_transaction.save()
            messages.success(request, 'Transaction modifiée avec succès.')
            return redirect('transaction_detail', transaction_id=transaction.id)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"Error in {field}: {error}")
            messages.error(request, 'Soumission du formulaire invalide. Se il vous plaît corriger les erreurs ci-dessous.')
    else:
        form = TransactionForm(instance=transaction)
    user_account = UserAccount.objects.get(user=request.user)
    return render(request, 'pages/transaction_modify.html', {
        'transaction': transaction,
        'form': form,
        'user_photo': user_account.photo.url if user_account.photo else None,
    })
def calculate_balance(user_account):
    return user_account.soldePris - abs(user_account.soldeDepense)

@login_required
def reset_account(request):
    if request.method == 'POST':
        user_account = get_object_or_404(UserAccount, user=request.user)
        
        # Supprimer toutes les transactions
        Transaction.objects.filter(user=request.user).delete()

        # Réinitialiser les valeurs du compte
        user_account.soldePris = 0
        user_account.soldeDepense = 0
        user_account.balance = 0
        user_account.budget = 0
        user_account.budget_limit_active = False
        user_account.save()

        messages.success(request, 'Toutes les valeurs et transactions ont été réinitialisées..')
    return redirect('home')

@login_required
def home(request):
    try:
        # Tentative de récupérer le UserAccount associé à l'utilisateur actuel
        user_account = UserAccount.objects.get(user=request.user)
    except UserAccount.DoesNotExist:
        # Si UserAccount n'existe pas, créez-le
        user_account = UserAccount.objects.create(user=request.user)
        # Vous souhaiterez peut-être ajouter plus de champs au compte utilisateur lors de la création
        
    if 'activate_budget_limit' in request.POST:
            user_account = UserAccount.objects.get(user=request.user)
            solde_depense_abs = abs(user_account.soldeDepense)
            user_account.budget = solde_depense_abs
            user_account.budget_limit_active = True
            user_account.save()
            return redirect('home')
    elif 'deactivate_budget_limit' in request.POST:
            user_account = UserAccount.objects.get(user=request.user)
            user_account.budget_limit_active = False
            user_account.save()
            return redirect('home')
    query = request.GET.get('query')
    if query:
        transactions = Transaction.objects.filter(
            user=request.user,
            title__icontains=query  # Adjust this field based on your Transaction model
        )
    else:
        transactions = Transaction.objects.filter(user=request.user).order_by('-date')
        
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
    solde_depense = +user_account.soldeDepense 
    budget = user_account.budget
     
    rest_budget = budget - abs(solde_depense)
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
        'query':query,
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

    # Vérifiez si la demande concerne le téléchargement d'un rapport
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
        return download_csv(transactions, user_account)
    elif file_format == 'xlsx':
        return download_xlsx(transactions, user_account)
    elif file_format == 'pdf':
        return download_pdf(transactions, user_account)
    else:
        messages.error(request, 'Invalid file format.')
        return redirect('rapport')
def download_csv(transactions, user_account):
    response = HttpResponse(content_type='text/csv')
    
    # Generate a timestamp
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    
    # Generate the filename
    filename = f'{user_account.user.username}_EcoSage-rapport_{timestamp}.csv'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    writer = csv.writer(response)
    writer.writerow(['Title', 'Amount', 'Category', 'Details', 'Date'])

    for transaction in transactions:
        writer.writerow([transaction.title, transaction.amount, transaction.category, transaction.details, transaction.date])

    # Calculate totals
    total_amount = sum(transaction.amount for transaction in transactions)
    total_solde_depense = abs(user_account.soldeDepense)
    total_solde_pris = user_account.soldePris
    total_balance = user_account.balance

    # Add totals to the CSV
    writer.writerow([])  # Add an empty row for spacing
    writer.writerow(['Total Amount:', total_amount])
    writer.writerow(['Total Solde Depensé:', total_solde_depense])
    writer.writerow(['Total Solde Pris:', total_solde_pris])
    writer.writerow(['Total Balance:', total_balance])

    return response
def download_xlsx(transactions, user_account):
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    
    # Generate a timestamp
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    
    # Generate the filename
    filename = f'{user_account.user.username}_EcoSage-rapport_{timestamp}.xlsx'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    workbook = xlsxwriter.Workbook(response, {'in_memory': True})
    worksheet = workbook.add_worksheet()

    # Add headers
    headers = ['Title', 'Amount', 'Category', 'Details', 'Date']
    header_format = workbook.add_format({'bold': True, 'bg_color': '#4287f5', 'border': 2})
    for col_num, header in enumerate(headers):
        worksheet.write(0, col_num, header, header_format)

    # Add data
    data_format = workbook.add_format({'border': 2})
    for row_num, transaction in enumerate(transactions, start=1):
        worksheet.write(row_num, 0, transaction.title, data_format)
        worksheet.write(row_num, 1, transaction.amount, data_format)
        worksheet.write(row_num, 2, transaction.category, data_format)
        worksheet.write(row_num, 3, transaction.details, data_format)
        worksheet.write(row_num, 4, str(transaction.date), data_format)

    # Set column widths
    # Set column widths
    column_widths = [len(header) for header in headers]  # Initialize with header lengths
    for transaction in transactions:
        for i, header in enumerate(headers):
            value = getattr(transaction, header.lower())  # Get attribute value dynamically
            if len(str(value)) > column_widths[i]:
                column_widths[i] = len(str(value))

    for i, width in enumerate(column_widths):
        worksheet.set_column(i, i, width + 2)  # Add some padding

    
    # Calculate totals and add them to the XLSX
    total_amount = sum(transaction.amount for transaction in transactions)
    total_solde_depense = abs(user_account.soldeDepense)
    total_solde_pris = user_account.soldePris
    total_balance = user_account.balance

    row_num += 2  # Add a couple of empty rows for spacing
    worksheet.write(row_num, 0, 'Total Amount:', data_format)
    worksheet.write(row_num, 1, total_amount, data_format)
    worksheet.write(row_num + 1, 0, 'Total Solde Depensé:', data_format)
    worksheet.write(row_num + 1, 1, total_solde_depense, data_format)
    worksheet.write(row_num + 2, 0, 'Total Solde Pris:', data_format)
    worksheet.write(row_num + 2, 1, total_solde_pris, data_format)
    worksheet.write(row_num + 3, 0, 'Total Balance:', data_format)
    worksheet.write(row_num + 3, 1, total_balance, data_format)

    workbook.close()
    return response
def download_pdf(transactions, user_account):
    response = HttpResponse(content_type='application/pdf')
    
    # Generate a timestamp
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    
    # Generate the filename
    filename = f'{user_account.user.username}_EcoSage-rapport_{timestamp}.pdf'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    pdf = canvas.Canvas(response, pagesize=letter)
    pdf.setTitle('EcoSage Rapport ')

    # Add user photo if available
    if user_account.photo:
        user_photo_path = user_account.photo.path
        pdf.drawImage(ImageReader(user_photo_path), 30, 650, width=100, height=100, preserveAspectRatio=True)

    # Define starting position and font size
    x, y = 30, 600
    font_size = 12
    
    # Header
    pdf.setFont("Helvetica-Bold", font_size)
    pdf.drawString(x, y, 'Title')
    pdf.drawString(x + 100, y, 'Amount')
    pdf.drawString(x + 200, y, 'Category')
    pdf.drawString(x + 300, y, 'Details')
    pdf.drawString(x + 400, y, 'Date')

    # Add data
    font_size = 10  # Reset font size for data
    y -= 20  # Move to the next row
    pdf.setFont("Helvetica", font_size)
    for transaction in transactions:
        pdf.drawString(x, y, transaction.title[:20])  # Adjust text length for the title
        pdf.drawString(x + 100, y, str(transaction.amount))
        pdf.drawString(x + 200, y, transaction.category[:20])  # Adjust text length for the category
        pdf.drawString(x + 300, y, transaction.details[:20])  # Adjust text length for the details
        pdf.drawString(x + 400, y, str(transaction.date))
        y -= 20

        if y < 50:  # New page if data exceeds the current page
            pdf.showPage()
            x, y = 30, 750  # Reset coordinates
            pdf.setFont("Helvetica-Bold", font_size)
            pdf.drawString(x, y, 'Title')
            pdf.drawString(x + 100, y, 'Amount')
            pdf.drawString(x + 200, y, 'Category')
            pdf.drawString(x + 300, y, 'Details')
            pdf.drawString(x + 400, y, 'Date')
            font_size = 10  # Reset font size for data
            y -= 20  # Move to the next row

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
            solde_depense_abs = abs(user_account.soldeDepense)
            user_account.budget = solde_depense_abs
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
                messages.error(request, 'Échec de la mise à jour de la photo de profil.')
        elif 'username' in request.POST:
            username_form = UsernameForm(request.POST, instance=request.user)
            if username_form.is_valid():
                username_form.save()
                
            else:
                messages.error(request, 'Échec de la mise à jour de le Username.')
        elif 'old_password' in request.POST:
            password_form = UserPasswordChangeForm(user=request.user, data=request.POST)
            if password_form.is_valid():
                password_form.save()
                
            else:
                messages.error(request, 'Échec de la mise à jour du mot de passe.')
        elif 'budget' in request.POST:
            budget_form = BudgetForm(request.POST)
            if budget_form.is_valid():
                user_account = UserAccount.objects.get(user=request.user)
                entered_budget = budget_form.cleaned_data['budget']
                if entered_budget >= user_account.soldeDepense:
                    user_account.budget = entered_budget
                    user_account.save()
                    messages.success(request, 'Budget mis à jour avec succès.')
                else:
                    messages.error(request, 'Échec de la mise à jour du budget. Le budget saisi ne peut pas être supérieur au solde dépensé.')
            else:
                messages.error(request, 'Échec de la mise à jour du budget.')
        return redirect('settings')
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
            messages.error(request, 'Montant invalide. S\'il vous plait, entrez un nombre valide.')
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
            amount = abs(Decimal(request.POST['amount']))  # Convert to Decimal
        except (ValueError, InvalidOperation):
            messages.error(request, 'Montant invalide. S\'il vous plait, entrez un nombre valide.')
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
