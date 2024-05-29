from django.db import models
from django.contrib.auth.models import User

class UserAccount(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    initial_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    photo = models.ImageField(upload_to='user_photos/', null=True, blank=True)
    budget = models.DecimalField(max_digits=10, decimal_places=2, default=999999)
    budget_limit_active = models.BooleanField(default=False)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    soldePris = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    soldeDepense = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    

class Transaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=15)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=100)
    details = models.TextField()
    date = models.DateField()
    transaction_type = models.CharField(max_length=20, choices=[('PRIS', 'Pris'), ('DONNE', 'Donné')])

    def __str__(self):
        return f"{self.transaction_type} {self.amount} DH on {self.date}"
