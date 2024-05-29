from django.urls import path
from . import views 
from django.contrib.auth import views as auth_views

urlpatterns =[
    path('', views.login,name='login'),
    path('forgot',views.forgot,name="forgot"),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('register', views.register, name='register'),
]