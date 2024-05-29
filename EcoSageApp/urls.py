from django.urls import path
from . import views 
from django.conf import settings
from django.conf.urls.static import static

urlpatterns =[
    path('', views.home,name='home'),
    path('rapport', views.rapport, name='rapport'),
    path('download_report/<str:file_format>/', views.download_report, name='download_report'),
    path('statistiques', views.statistiques, name='statistiques'),
    path('profile',views.profile,name='profile'),
    path('settings',views.settings,name='settings'),
    path('jai_pris/', views.jai_pris, name='jai_pris'),
    path('jai_donne/', views.jai_donne, name='jai_donne'),
    path('transaction/<int:transaction_id>/', views.transaction_detail, name='transaction_detail'),
    path('transaction/<int:transaction_id>/modify/', views.transaction_modify, name='transaction_modify'),
    path('search_transactions/', views.search_transactions, name='search_transactions'),
    
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)