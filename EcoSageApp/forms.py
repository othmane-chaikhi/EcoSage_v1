from django import forms

class UserEditForm(forms.Form):
    first_name = forms.CharField(max_length=100, required=False)
    last_name = forms.CharField(max_length=100, required=False)
    email = forms.EmailField(required=False)
    # Add more fields as needed

from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordChangeForm

class ProfilePhotoForm(forms.Form):
    photo = forms.ImageField(label='Profile Photo')

class UsernameForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username']

class UserPasswordChangeForm(PasswordChangeForm):
    pass

from .models import UserAccount
class BudgetForm(forms.ModelForm):
    class Meta:
        model = UserAccount
        fields = ['budget']


class BudgetLimitForm(forms.Form):
    activate_budget_limit = forms.BooleanField(label='Activate Budget Limit', required=False)
    deactivate_budget_limit = forms.BooleanField(label='Deactivate Budget Limit', required=False)
from .models import Transaction

class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['title', 'amount', 'category', 'details', 'date', 'transaction_type']