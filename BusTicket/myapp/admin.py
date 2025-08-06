

# Register your models here.
from django.contrib import admin

from .models import Operator,Bus,Route,Schedule,Seat_Status,Booking,Ticket,Payment,Admin,User
# Register your models here.


admin.site.register(User)
admin.site.register(Operator)
admin.site.register(Bus)
admin.site.register(Route)
admin.site.register(Schedule)
admin.site.register(Seat_Status)
admin.site.register(Booking)
admin.site.register(Ticket)
admin.site.register(Payment)
admin.site.register(Admin)
# admin.site.register(Book)
# admin.site.register(Feedback)
