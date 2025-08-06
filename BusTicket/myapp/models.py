from email.policy import default

from django.db import models

# Create your models here.
# Create your models here.
from django.db import models
from django.utils import timezone

# Create your models here.
class Operator(models.Model):
    operator_id = models.CharField(primary_key=True, max_length=10)
    operator_name = models.CharField(max_length=50,default='')
    del_flag = models.IntegerField(default=0)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.operator_name

class Bus(models.Model):
    bus_id = models.CharField(primary_key=True,max_length=10)
    license_no = models.CharField(max_length=15,default='')
    seat_capacity = models.IntegerField(default=30)
    bus_type = models.CharField(max_length = 10,default='Standard')
    del_flag = models.IntegerField(default=0)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    operator = models.ForeignKey(Operator,on_delete=models.CASCADE)

    class Meta:
        verbose_name_plural = "List of Buses"

    def __str__(self):
        return self.license_no

class Route(models.Model):
    route_id = models.CharField(primary_key=True,max_length=20)
    origin = models.CharField(max_length=30)
    destination = models.CharField(max_length=30)
    del_flag = models.IntegerField(default=0)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    class Meta:
        verbose_name_plural = "Routes"

    def __str__(self):
        return f"{self.origin} -> {self.destination}"

class Schedule(models.Model):
    schedule_id = models.CharField(primary_key=True,max_length=20)
    bus = models.ForeignKey(Bus,on_delete=models.CASCADE)
    route = models.ForeignKey(Route,on_delete=models.CASCADE)
    date = models.DateField()
    time = models.TimeField()
    price = models.DecimalField(max_digits=5,decimal_places=0)
    del_flag = models.IntegerField(default=0)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    class Meta:
        verbose_name_plural = "Schedules"

    def __str__(self):
        return self.schedule_id


class Seat_Status(models.Model):
    seat_no = models.CharField(max_length=5)
    schedule = models.ForeignKey(Schedule,on_delete=models.CASCADE)
    seat_status = models.CharField(max_length=20,default='Available')
    booking = models.ForeignKey('Booking',on_delete=models.CASCADE,null=True,blank=True)
    class Meta:
        unique_together = ('schedule','seat_no')
    def __str__(self):
        return f"{self.schedule.schedule_id} - {self.seat_no} ({self.seat_status})"

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

class Booking(models.Model):
    booking_id = models.CharField(max_length=20,primary_key=True)
    schedule = models.ForeignKey(Schedule,on_delete=models.CASCADE)
    customer = models.ForeignKey(User,on_delete=models.CASCADE)
    seat_numbers = models.CharField(max_length=100)
    booked_time = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        self.booking_id

class Ticket(models.Model):
    ticket_id = models.CharField(max_length=20,primary_key=True)
    booking = models.OneToOneField(Booking,on_delete=models.CASCADE)
    total_seat = models.IntegerField()
    total_amount = models.DecimalField(max_digits=6,decimal_places=0)
    created_date = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.ticket_id

class Payment(models.Model):
    PAYMENT_METHODS = [
        ('KP','KPay'),
        ('WP','WavePay'),
    ]
    payment_id = models.CharField(max_length=20,primary_key=True)
    ticket = models.OneToOneField(Ticket,on_delete=models.CASCADE)
    payment_method = models.CharField(max_length=2,choices=PAYMENT_METHODS)
    created_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.payment_id

class Admin(models.Model):
    email = models.EmailField()
    password = models.CharField(max_length=30)
    def __str__(self):
        return self.email
#
# class Book(models.Model):
#     BOOKED = 'B'
#     CANCELLED = 'C'
#
#     TICKET_STATUSES = ((BOOKED, 'Booked'),
#                        (CANCELLED, 'Cancelled'),)
#     email = models.EmailField()
#     name = models.CharField(max_length=30)
#     userid =models.DecimalField(decimal_places=0, max_digits=2)
#     busid=models.DecimalField(decimal_places=0, max_digits=2)
#     bus_name = models.CharField(max_length=30)
#     source = models.CharField(max_length=30)
#     dest = models.CharField(max_length=30)
#     nos = models.DecimalField(decimal_places=0, max_digits=2)
#     price = models.DecimalField(decimal_places=2, max_digits=6)
#     date = models.DateField()
#     time = models.TimeField()
#     seat_numbers = models.CharField(max_length=100, null=True, blank=True)
#     status = models.CharField(choices=TICKET_STATUSES, default=BOOKED, max_length=2)
#
#     class Meta:
#         verbose_name_plural = "List of Books"
#     def __str__(self):
#         return self.email
# from django.db import models
#
# class Feedback(models.Model):
#     name = models.CharField(max_length=100)
#     email = models.EmailField()
#     rating = models.IntegerField(choices=[
#         (1, 'Very Poor'),
#         (2, 'Poor'),
#         (3, 'Average'),
#         (4, 'Good'),
#         (5, 'Excellent')
#     ])
#     bus_number = models.CharField(max_length=50, blank=True, null=True)  # Optional field
#     feedback = models.TextField()
#     submitted_on = models.DateTimeField(auto_now_add=True)
#
#     def __str__(self):
#         return f"{self.name} ({self.rating})"

