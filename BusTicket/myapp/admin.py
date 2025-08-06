

# Register your models here.
from django.contrib import admin

from .models import User,Operator,Bus
# Register your models here.


admin.site.register(User)
admin.site.register(Operator)
admin.site.register(Bus)
# admin.site.register(Book)
# admin.site.register(Feedback)
