from django.db import models

# Create your models here.
class user(models.Model):
    username = models.CharField(max_length=20)
    password = models.CharField(max_length=15)
    # email = models.EmailField()
    # bqit hna  to be continue ^_^ models