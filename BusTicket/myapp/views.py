
from django.shortcuts import render
from django.db.models import Q
from datetime import datetime
from django.contrib import messages
from django.shortcuts import render
from decimal import Decimal
from django.db import IntegrityError
from django.contrib.auth import login
from django.template.context_processors import request

# from .models import Feedback
# Create your views here.
from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from .models import User, Operator, Bus, Route, Schedule,Booking,Ticket
from django.urls import reverse
from django.contrib.auth import authenticate, login, logout
# from django.contrib.auth.models import User
from .forms import UserLoginForm, UserRegisterForm
from django.contrib.auth.decorators import login_required
from decimal import Decimal
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from django.http import HttpResponse
from .models import Booking
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
import qrcode
from django.shortcuts import render, get_object_or_404
from io import BytesIO
from .forms import BookingForm
from .forms import OperatorForm
from .forms import RouteForm
from .forms import BusForm
from django.shortcuts import render
from datetime import datetime
from .models import Route, Schedule

# Create your views here.


# In home page, when you enter origin,destination and date this function will search for available routes

def search_routes(request):
    # Always provide dropdown lists
    origins = Route.objects.values_list('origin', flat=True).distinct()
    destinations = Route.objects.values_list('destination', flat=True).distinct()

    context = {'origins': origins, 'destinations': destinations}

    # Accept both GET and POST (GET useful for header quick-search)
    data = request.GET if request.method == 'GET' and request.GET else request.POST

    if data:
        origin_r = data.get('origin', '').strip()
        dest_r = data.get('destination', '').strip()
        # allow either 'date' (base) or 'departure_date' (header)
        date_r = data.get('date') or data.get('departure_date')
        number_of_seats = data.get('number_of_seats')


        # If the form came from header and used 'to' param, support that:
        if not dest_r and data.get('to'):
            dest_r = data.get('to').strip()

        # Save selected values for repopulating form
        context.update({
            'data':data,
            'selected_origin': origin_r,
            'selected_destination': dest_r,
            'selected_date': date_r,
            'number_of_seats':number_of_seats,
        })

        # Validate required fields
        if not (origin_r and dest_r and date_r):
            context.update({'error': 'Please enter origin, destination and date.', 'data': data})
            return render(request, 'base.html', context)

        try:
            date_obj = datetime.strptime(date_r, "%Y-%m-%d").date()
        except ValueError:
            context.update({'error': 'Invalid date format.', 'data': data})
            return render(request, 'base.html', context)

        schedules = Schedule.objects.filter(
            route__origin__iexact=origin_r,
            route__destination__iexact=dest_r,
            date=date_obj,
            del_flag=0,
            route__del_flag=0,
            bus__del_flag=0
        )

        if schedules.exists():
            return render(request, 'available_routes.html', {
                'schedules': schedules,
                'origins':origins,
                'destinations':destinations,
                'selected_origin':origin_r,
                'selected_destination':dest_r,
                'selected_date':date_r,
                'selected_seat':number_of_seats,
            })
        else:
            context.update({'error': 'No available Bus Schedule for entered Route and Date', 'data': data})
            return render(request, 'base.html', {'context':context})

    # GET with no query params -> show base form (empty)
    return render(request, 'base.html', context)

from django.http import HttpResponse

def submit_seats(request, schedule_id):
    if request.method == "POST":
        selected_seats = request.POST.getlist('selected_seats')
        return HttpResponse(f"Selected seats: {', '.join(selected_seats)}")
    return HttpResponse(status=405)



def user_login(request):
    if request.user.is_authenticated:
        return render(request, 'home.html')
    else:
        return render(request, 'signin.html')



def home(request):
    bookings = Bus.objects.all()
    return render(request,'base.html',{'bookings':bookings})


#
#
# @login_required(login_url='signin')
# def bookings(request):
#     context = {}
#     if request.method == 'POST':
#         id_r = request.POST.get('bus_id')
#         seats_r = int(request.POST.get('no_seats'))
#         bus = Bus.objects.get(id=id_r)
#         if bus:
#             if bus.rem > int(seats_r):
#                 seat_numbers = [str(i) for i in range(int(bus.nos) - int(bus.rem) + 1, int(bus.nos) - int(bus.rem) + seats_r + 1)]
#                 seat_numbers_str = ', '.join(seat_numbers)
#                 name_r = bus.bus_name
#                 cost = int(seats_r) * bus.price
#                 source_r = bus.source
#                 dest_r = bus.dest
#                 nos_r = Decimal(bus.nos)
#                 price_r = bus.price
#                 date_r = bus.date
#                 time_r = bus.time
#                 username_r = request.user.username
#                 email_r = request.user.email
#                 userid_r = request.user.id
#                 rem_r = bus.rem - seats_r
#                 Bus.objects.filter(id=id_r).update(rem=rem_r)
#                 book = Book.objects.create(name=username_r, email=email_r, userid=userid_r, bus_name=name_r,
#                                            source=source_r, busid=id_r,
#                                            dest=dest_r, price=price_r, nos=seats_r, date=date_r, time=time_r,
#                                            status='BOOKED',seat_numbers=seat_numbers_str)
#                 print('------------book id-----------', book.id)
#                 # book.save()
#                 return render(request, 'bookings.html', locals())
#             else:
#                 context["error"] = "Sorry select fewer number of seats"
#                 return render(request, 'findbus.html', context)
#
#     else:
#         return render(request, 'findbus.html')
# def booking_confirmation(request, booking_id):
#     booking = Book.objects.get(id=booking_id)
#     return render(request, 'confirmation.html', {'book': booking})
#
#
#
# @login_required(login_url='signin')
# def cancellings(request):
#     context = {}
#     if request.method == 'POST':
#         id_r = request.POST.get('bus_id')
#         seats_r = int(request.POST.get('no_seats'))
#
#         try:
#             book = Book.objects.get(id=id_r)
#             bus = Bus.objects.get(id=book.busid)
#             rem_r = bus.rem + book.nos
#             Bus.objects.filter(id=book.busid).update(rem=rem_r)
#             #nos_r = book.nos - seats_r
#             Book.objects.filter(id=id_r).update(status='CANCELLED')
#             Book.objects.filter(id=id_r).update(nos=0)
#             messages.success(request, "Booked Bus has been cancelled successfully.")
#             return redirect(seebookings)
#         except Book.DoesNotExist:
#             context["error"] = "Sorry You have not booked that bus"
#             return render(request, 'error.html', context)
#     else:
#         return render(request, 'findbus.html')
#
# def payment_process(request, booking_id):
#     if request.method == 'POST':
#         name = request.POST.get('name')
#         email = request.POST.get('email')
#         card_number = request.POST.get('card_number')
#         expiry_date = request.POST.get('expiry_date')
#         cvv = request.POST.get('cvv')
#         insurance = request.POST.get('insurance', 'no')
#
#         # Validate the fields (You can add more sophisticated validation as needed)
#         if not (name and email and card_number and expiry_date and cvv):
#             messages.error(request, "All fields are mandatory.")
#             return render(request, 'payment.html', {'total_amount': total_amount, 'booking_id': booking_id})
#
#
#         return redirect('payment_success', booking_id=booking_id)
#
#     # If GET request, just render the payment page
#     return render(request, 'payment.html', {'total_amount': total_amount, 'booking_id': booking_id})
#
#
#
# @login_required(login_url='signin')
# def seebookings(request,new={}):
#     context = {}
#     id_r = request.user.id
#     book_list = Book.objects.filter(userid=id_r)
#     if book_list:
#         return render(request, 'booklist.html', locals())
#     else:
#         context["error"] = "Sorry no buses booked"
#         return render(request, 'findbus.html', context)
#
#
def signup(request):
    context = {}
    if request.method == 'POST':
        name_r = request.POST.get('name')
        email_r = request.POST.get('email')
        password_r = request.POST.get('password')
        nrc_r = request.POST.get('nrc')
        address_r = request.POST.get('address')
        phone_no_r = request.POST.get('phone_no')

        # Check if the username already exists
        if User.objects.filter(name=name_r).exists():
            context["error"] = "Username already exists, please choose another one."
            return render(request, 'signup.html', context)

        # Check if the email already exists
        if User.objects.filter(email=email_r).exists():
            context["error"] = "Email is already registered, please choose another one."
            return render(request, 'signup.html', context)
        if nrc_r and User.objects.filter(nrc=nrc_r).exists():
            context['error'] = "NRC already exists."
            return render(request, 'signup.html', context)

        try:
            user = User.objects.create(
                name=name_r,
                email=email_r,
                password=make_password(password_r),
                nrc=nrc_r,
                address=address_r,
                phone_no=phone_no_r
            )
            if user:
                login(request, user)
                return render(request, 'thank.html')
        except IntegrityError:
            context["error"] = "An error occurred. Please try again."
            return render(request, 'signup.html', context)

    return render(request, 'signup.html', context)

def signin(request):
    context = {}
    if request.method == 'POST':
        name_r = request.POST.get('name')
        password_r = request.POST.get('password')
        user = authenticate(request, username=name_r, password=password_r)
        if user:
            login(request, user)
            # username = request.session['username']
            context["user"] = name_r
            context["id"] = request.user.id
            return render(request, 'success.html', context)
            # return HttpResponseRedirect('success')
        else:
            context["error"] = "Provide valid credentials"
            return render(request, 'signin.html', context)
    else:
        context["error"] = "You are not logged in"
        return render(request, 'signin.html', context)
# @login_required(login_url='signin')
# def download_ticket(request, booking_id):
#     booking = Book.objects.get(id=booking_id)
#
#     response = HttpResponse(content_type='application/pdf')
#     response['Content-Disposition'] = f'attachment; filename="ticket_{booking_id}.pdf"'
#
#     pdf = canvas.Canvas(response, pagesize=letter)
#     pdf.setTitle("Bus Ticket")
#
#     # Draw Ticket Border
#     pdf.setStrokeColor(colors.black)
#     pdf.setLineWidth(3)
#     pdf.rect(50, 430, 500, 320, stroke=True, fill=False)  # Increased width and height
#
#     # Add Title
#     pdf.setFont("Helvetica-Bold", 20)
#     pdf.drawCentredString(300, 730, "Bus Ticket")
#     logo_path = "https://i.pinimg.com/originals/e2/1c/b5/e21cb58cda4ccf597b05d2048b483c0d.jpg"  # Ensure the correct path to the logo
#     logo_img = ImageReader(logo_path)
#     pdf.drawImage(logo_img, 50, 750, width=100, height=50)
#     # Add Booking Information
#     pdf.setFont("Helvetica-Bold", 14)
#     pdf.drawString(80, 680, "Booking ID:")
#     pdf.drawString(80, 660, "Name:")
#     pdf.drawString(80, 640, "Email:")
#     pdf.drawString(80, 620, "Bus Name:")
#     pdf.drawString(80, 600, "Source:")
#     pdf.drawString(80, 580, "Destination:")
#     pdf.drawString(80, 560, "Date:")
#     pdf.drawString(80, 540, "Time:")
#     pdf.drawString(80, 520, "Seats:")
#     pdf.drawString(80, 500, "Seat Numbers:")
#     pdf.drawString(80, 480, "Total Price:")
#
#     pdf.setFont("Helvetica", 14)
#     pdf.drawString(200, 680, f"{booking.id}")
#     pdf.drawString(200, 660, f"{booking.name}")
#     pdf.drawString(200, 640, f"{booking.email}")
#     pdf.drawString(200, 620, f"{booking.bus_name}")
#     pdf.drawString(200, 600, f"{booking.source}")
#     pdf.drawString(200, 580, f"{booking.dest}")
#     pdf.drawString(200, 560, f"{booking.date}")
#     pdf.drawString(200, 540, f"{booking.time}")
#     pdf.drawString(200, 520, f"{booking.nos}")
#     pdf.drawString(200, 500, f"{booking.seat_numbers}")
#     pdf.drawString(200, 480, f"RS.{booking.price * booking.nos}")
#
#     # Draw separation lines
#     pdf.setLineWidth(1)
#     pdf.line(50, 470, 550, 470)
#
#     # Generate QR Code with booking details
#     qr_data = f"Booking ID: {booking.id}\nName: {booking.name}\nEmail: {booking.email}\nBus Name: {booking.bus_name}\nSource: {booking.source}\nDestination: {booking.dest}\nDate: {booking.date}\nTime: {booking.time}\nSeats: {booking.nos}\nSeat Numbers: {booking.seat_numbers}\nTotal Price: RS.{booking.price * booking.nos}"
#     qr = qrcode.QRCode(
#         version=1,
#         error_correction=qrcode.constants.ERROR_CORRECT_L,
#         box_size=10,
#         border=4,
#     )
#     qr.add_data(qr_data)
#     qr.make(fit=True)
#
#     img = qr.make_image(fill='black', back_color='white')
#     buffer = BytesIO()
#     img.save(buffer)
#     qr_img = ImageReader(buffer)
#     pdf.drawImage(qr_img, 400, 500, width=100, height=100)  # Adjust the position as needed
#
#     # Add Footer
#     pdf.setFont("Helvetica", 10)
#     pdf.drawCentredString(300, 400, "Thank you for choosing our service!")
#
#     pdf.showPage()
#     pdf.save()
#
#     return response
#
def signout(request):
    context = {}
    logout(request)
    context['error'] = "You have been logged out"
    return render(request, 'signin.html', context)

# def success(request):
#     context = {}
#     context['user'] = request.user
#     return render(request, 'success.html', context)
# def payment_page(request, booking_id):
#     booking = get_object_or_404(Book, id=booking_id)
#     total_amount = booking.price * booking.nos  # Calculate total amount
#     context = {
#         'booking': booking,
#         'total_amount': total_amount,
#     }
#     return render(request, 'payement.html', context)
# def payment_success(request, booking_id):
#     booking = get_object_or_404(Book, id=booking_id)
#     context = {'booking': booking}
#     return render(request, 'payement_success.html', context)
# # Assuming there's a Booking model
#
# def FeedbackForm(request, booking_id):
#     # Get the specific booking (optional, based on your use case)
#     booking = get_object_or_404(Book, id=booking_id)
#
#     if request.method == 'GET':
#         return render(request, 'feedbackform.html', {'booking': booking})
#     else:
#         # Save the feedback
#         Feedback(
#             name=request.POST.get('name'),
#             email=request.POST.get('email'),
#             rating=request.POST.get('rating'),
#             bus_number=request.POST.get('bus_number'),
#             feedback=request.POST.get('feedback')
#         ).save()
#
#         feedback_list = Feedback.objects.all()
#         return render(request, 'feedback_list.html', {'feedbacks': feedback_list})
#
# def FeedbackList(request):
#     feedback_list = Feedback.objects.all()
#     return render(request, 'feedback_list.html', {'feedbacks': feedback_list})
#
def seat_selection(request,schedule_id):
    selected_bus = Schedule.objects.get(id=schedule_id)
    # source = request.GET.get('from')
    # dest = request.GET.get('to')
    # date = request.GET.get('departure_date')
    seats = request.GET.get('number_of_seats')
    seats = int(seats)
    total_price=Decimal(seats)*selected_bus.price
    context={
        'bus':selected_bus,
        'origin':selected_bus.route.origin,
        'destination':selected_bus.route.destination,
        'date':selected_bus.date,
        'seats':seats,
        'total_price':total_price,
        'schedule_id':selected_bus.id,
    }
    return render(request, 'seat_selection.html',context)




# Admin Dashboard
def admin_dashboard(request):
    no_of_users = User.objects.filter(del_flag = 0).count()
    no_of_buses = Bus.objects.filter(del_flag = 0).count()
    no_of_routes = Route.objects.filter(del_flag=0).count()
    no_of_operators = Operator.objects.filter(del_flag=0).count()
    no_of_schedules = Schedule.objects.filter(del_flag=0).count()
    no_of_bookings = Booking.objects.all().count()
    no_of_tickets = Ticket.objects.all().count()

    return render(request,'admin/dashboard.html',{
        'no_of_users' : no_of_users,
        'no_of_buses' : no_of_buses,
        'no_of_routes' : no_of_routes,
        'no_of_operators' : no_of_operators,
        'no_of_schedules' : no_of_schedules,
        'no_of_bookings' : no_of_bookings,
        'no_of_tickets' : no_of_tickets

    })

def user_home(request):
    users = User.objects.all().order_by('name')
    return render(request,'admin/user_home.html',{'users' : users})

def soft_delete_user(request,user_id):
    user_info = User.objects.get(user_id=user_id)
    if user_info.del_flag == 0:
        user_info.del_flag = 1
        user_info.save()
    else:
        user_info.del_flag = 0
        user_info.save()

    return redirect('user_home')


# operator home page in admin
def operator_home(request):
    search_query = request.GET.get('search', '')
    operators = Operator.objects.all()
    if search_query:
        operators = operators.filter(Q(operator_name__icontains=search_query))
    context = {
    'operators': operators,
    'search_query': search_query,
    }
    return render(request, 'admin/operator_home.html', context)



# route home page in admin
def route_home(request):
    origin_query = request.GET.get('origin', '')
    destination_query = request.GET.get('destination', '')

    routes = Route.objects.all()

    if origin_query:
        routes = routes.filter(Q(origin__icontains=origin_query))

    if destination_query:
        routes = routes.filter(Q(destination__icontains=destination_query))

    context = {
        'routes': routes,
        'origin_query': origin_query,
        'destination_query': destination_query,
    }
    return render(request, 'admin/route_home.html', context)

def add_operator(request):
    if request.method == 'POST':
        operator_form = OperatorForm(request.POST)
        if operator_form.is_valid():
            operator_form.save()
            return HttpResponseRedirect('/admindashboard/operator_home/')
    else:
        operator_form = OperatorForm()

    return render(request,'admin/operator_add_form.html',{'operator_form' : operator_form})

def update_operator(request,operator_id):
    operator_info = Operator.objects.get(pk = operator_id)

    if request.method == 'POST':
        operator_form = OperatorForm(request.POST, instance=operator_info)
        if operator_form.is_valid():
            operator_form.save()
            return redirect('operator_home')
    else:
        operator_form = OperatorForm(instance=operator_info)

    return render(request,'admin/operator_update.html',{'operator_form' : operator_form})

def delete_operator(request,operator_id):
    operator_info = Operator.objects.get(id=operator_id)
    if operator_info.del_flag == 0:
        operator_info.del_flag = 1
        operator_info.save()
    else:
        operator_info.del_flag = 0
        operator_info.save()

    return redirect('operator_home')

# route home page in admin
from django.shortcuts import render
from django.db.models import Q
from .models import Route  # Assuming your model is named Route


def route_home(request):
    origin_query = request.GET.get('origin', '')
    destination_query = request.GET.get('destination', '')

    routes = Route.objects.all()

    if origin_query:
        routes = routes.filter(Q(origin__icontains=origin_query))

    if destination_query:
        routes = routes.filter(Q(destination__icontains=destination_query))

    # This is the correct way to order the queryset
    routes = routes.order_by('-updated_date')

    context = {
        'routes': routes,
        'origin_query': origin_query,
        'destination_query': destination_query,
    }
    return render(request, 'admin/route_home.html', context)


def add_route(request):
    if request.method == 'POST':
        route_form = RouteForm(request.POST)
        if route_form.is_valid():
            route_form.save()
            return redirect('route_home')
    else:
        route_form = RouteForm()
    return render(request, 'admin/route_add_form.html', {'form': route_form})

def update_route(request,route_id):
    route_info = Route.objects.get(pk = route_id)

    if request.method == 'POST':
        route_form = RouteForm(request.POST, instance=route_info)
        if route_form.is_valid():
            route_form.save()
            return redirect('route_home')
    else:
        route_form = RouteForm(instance=route_info)

    return render(request,'admin/route_update.html',{'route_form' : route_form})

def delete_route(request,route_id):
    route_info = Route.objects.get(id=route_id)
    if route_info.del_flag == 0:
        route_info.del_flag = 1
        route_info.save()
    else:
        route_info.del_flag = 0
        route_info.save()

    return redirect('route_home')

# Admin Bus Section
def bus_home(request):
    license_query = request.GET.get('license_no', '')
    operator_query = request.GET.get('operator', '')

    buses = Bus.objects.all()

    if license_query:
        buses = buses.filter(Q(license_no__icontains=license_query))

    if operator_query:
        buses = buses.filter(Q(operator__id=operator_query))

    buses = buses.order_by('-updated_date')
    operators = Operator.objects.all()

    context = {
        'buses': buses,
        'operators': operators,
        'license_query': license_query,
        'operator_query': operator_query,
    }

    return render(request, 'admin/bus_home.html', context)

def add_bus(request):
    if request.method == 'POST':
        bus_form = BusForm(request.POST)
        if bus_form.is_valid():
            bus_form.save()
            return redirect('bus_home')
    else:
        bus_form = BusForm()
    return render(request,'admin/bus_add_form.html',{'form' : bus_form})


def update_bus(request,bus_id):
    bus_info = Bus.objects.get(pk= bus_id)

    if request.method == 'POST':
        bus_form = BusForm(request.POST, instance=bus_info)
        if bus_form.is_valid():
            bus_form.save()
            return redirect('bus_home')
    else:
        bus_form = BusForm(instance=bus_info)

    return render(request,'admin/bus_update.html',{'bus_form':bus_form})

def delete_bus(request,bus_id):
    bus_info = Bus.objects.get(id=bus_id)
    if bus_info.del_flag == 0:
        bus_info.del_flag = 1
        bus_info.save()
    else:
        bus_info.del_flag = 0
        bus_info.save()

    return redirect('bus_home')