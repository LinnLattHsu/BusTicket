from email.policy import default

from django.db import models

# Create your models here.
# Create your models here.
from django.db import models
from django.utils import timezone

# Create your models here.
class Operator(models.Model):
    name = models.CharField(max_length=50,default='')
    del_flag = models.IntegerField(default=0)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

class Bus(models.Model):
    license_no = models.CharField(max_length=15,default='')
    seat_capacity = models.IntegerField(default=30)
    bus_type = models.CharField(max_length = 10,default='Standard')
    del_flag = models.IntegerField(default=0)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    operator_name = models.ForeignKey(Operator,on_delete=models.CASCADE)

    class Meta:
        verbose_name_plural = "Busses"

    def __str__(self):
        return self.license_no


class User(models.Model):
    user_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=30)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=30)
    nrc = models.CharField(max_length=30,unique=True,null=True)
    address = models.CharField(max_length=100,default='')
    phone_no = models.CharField(max_length=11,null=True)
    del_flag = models.IntegerField(default=0)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)


    class Meta:
        verbose_name_plural = "Users"

    def __str__(self):
        return self.name




class Book(models.Model):
    BOOKED = 'B'
    CANCELLED = 'C'

    TICKET_STATUSES = ((BOOKED, 'Booked'),
                       (CANCELLED, 'Cancelled'),)
    email = models.EmailField()
    name = models.CharField(max_length=30)
    userid =models.DecimalField(decimal_places=0, max_digits=2)
    busid=models.DecimalField(decimal_places=0, max_digits=2)
    bus_name = models.CharField(max_length=30)
    source = models.CharField(max_length=30)
    dest = models.CharField(max_length=30)
    nos = models.DecimalField(decimal_places=0, max_digits=2)
    price = models.DecimalField(decimal_places=2, max_digits=6)
    date = models.DateField()
    time = models.TimeField()
    seat_numbers = models.CharField(max_length=100, null=True, blank=True)
    status = models.CharField(choices=TICKET_STATUSES, default=BOOKED, max_length=2)

    class Meta:
        verbose_name_plural = "List of Books"
    def __str__(self):
        return self.email
from django.db import models

class Feedback(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    rating = models.IntegerField(choices=[
        (1, 'Very Poor'),
        (2, 'Poor'),
        (3, 'Average'),
        (4, 'Good'),
        (5, 'Excellent')
    ])
    bus_number = models.CharField(max_length=50, blank=True, null=True)  # Optional field
    feedback = models.TextField()
    submitted_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.rating})"

