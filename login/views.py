from django.shortcuts import render,redirect
from django.contrib.auth import authenticate, login as auth_login
from django.contrib import messages
from .forms import RegistrationForm
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User



def login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)
            return redirect('home')
        else :
            messages.error(request, 'La connexion a échoué. Veuillez réessayer.', extra_tags='login')
        
    return render(request, 'pages/login/index.html')
    
def forgot(request):
    return render(request ,'pages/login/forgot.html')


# views.py


def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            # Redirect to a success page or login page after successful registration
            return redirect('login')
        else :
            messages.error(request, 'Se il vous plaît corriger les erreurs ci-dessous..', extra_tags='login')
    else:
        form = UserCreationForm()
    return render(request, 'pages/login/register.html', {'form': form})
