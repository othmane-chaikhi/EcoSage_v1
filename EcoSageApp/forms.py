from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordChangeForm
from .models import UserAccount,Transaction
 
class UserEditForm(forms.Form):
    first_name = forms.CharField(max_length=100, required=False)
    last_name = forms.CharField(max_length=100, required=False)
    email = forms.EmailField(required=False)

class ProfilePhotoForm(forms.Form):
    photo = forms.ImageField(label='Profile Photo')

class UsernameForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username']

class UserPasswordChangeForm(PasswordChangeForm):
    pass

class BudgetForm(forms.ModelForm):
    class Meta:
        model = UserAccount
        fields = ['budget']
        widgets = {
            'budget': forms.NumberInput(attrs={'class': 'form-control'})
        }

class BudgetLimitForm(forms.Form):
    activate_budget_limit = forms.BooleanField(label='Activate Budget Limit', required=False)
    deactivate_budget_limit = forms.BooleanField(label='Deactivate Budget Limit', required=False)

class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['title', 'amount', 'category', 'details', 'date', 'transaction_type']