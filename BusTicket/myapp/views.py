import json

from django.shortcuts import render
from django.db.models import Q, Count
from datetime import datetime, date
from django.contrib import messages
from django.shortcuts import render
from decimal import Decimal
from django.db import IntegrityError, transaction
from django.contrib.auth import login
from django.template.context_processors import request
from django.shortcuts import render, redirect  # Ensure 'redirect' is imported
from decimal import Decimal
# Make sure you import all your relevant models here:
from .models import Schedule, Booking, Ticket  # Assuming Bus, Route are already in models.py
# from .models import Feedback
# Create your views here.
from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from .models import User, Operator, Bus, Route, Schedule,Booking,Ticket,Payment
from .models import Seat_Status
from django.urls import reverse
# from django.contrib.auth import authenticate, login, logout
# from django.contrib.auth.models import User
from .forms import UserLoginForm, UserRegisterForm, CustomUserCreationForm
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
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from .models import Booking, Schedule, User
from .forms import BookingForm
from .forms import OperatorForm
from .forms import RouteForm
from .forms import BusForm
from .forms import ScheduleForm,CustomUserChangeForm
from django.shortcuts import render
from datetime import datetime
from .models import Route, Schedule
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import AuthenticationForm
from .models import Admin
from django.contrib.admin.views.decorators import staff_member_required
from .forms import CustomUserAuthenticationForm
from django.contrib.auth import logout as auth_logout
from django.conf import settings
# Create your views here.


# In home page, when you enter origin,destination and date this function will search for available routes

def search_routes(request):
    # Always provide dropdown lists
    origins = Route.objects.values_list('origin', flat=True).distinct()
    destinations = Route.objects.values_list('destination', flat=True).distinct()
    operators = Operator.objects.filter(del_flag=0).order_by("operator_name")

    context = {
        'origins': origins,
        'destinations': destinations,
        'operators': operators,
    }

    # Accept both GET and POST
    data = request.GET if request.method == 'GET' and request.GET else request.POST

    if data:
        origin_r = data.get('origin', '').strip()
        dest_r = data.get('destination', '').strip()
        date_r = data.get('date') or data.get('departure_date')
        number_of_seats = data.get('number_of_seats')
        bus_type = data.get('bus_type')
        operator_name = data.get('operator_name')  # ✅ fixed

        if not dest_r and data.get('to'):
            dest_r = data.get('to').strip()

        context.update({
            'data': data,
            'selected_origin': origin_r,
            'selected_destination': dest_r,
            'selected_date': date_r,
            'number_of_seats': number_of_seats,
            'selected_bus_type': bus_type,
            'selected_operator': operator_name,
        })

        if not (origin_r and dest_r and date_r):
            context.update({'error': 'Please enter origin, destination and date.'})
            return render(request, 'base.html', context)

        try:
            date_obj = datetime.strptime(date_r, "%Y-%m-%d").date()
        except ValueError:
            context.update({'error': 'Invalid date format.'})
            return render(request, 'base.html', context)

        schedules = Schedule.objects.filter(
            route__origin__iexact=origin_r,
            route__destination__iexact=dest_r,
            date=date_obj,
            del_flag=0,
            route__del_flag=0,
            bus__del_flag=0
        )
        # Apply bus type filter
        if bus_type:
            schedules = schedules.filter(bus__bus_type__iexact=bus_type)

        # Apply operator filter
        if operator_name:
            schedules = schedules.filter(bus__operator__operator_name__iexact=operator_name)

        if schedules.exists():
            return render(request, 'available_routes.html', {
                'schedules': schedules,
                'origins': origins,
                'destinations': destinations,
                'operators': operators,  # ✅ added
                'selected_origin': origin_r,
                'selected_destination': dest_r,
                'selected_date': date_r,
                'selected_seat': number_of_seats,
                'selected_bus_type': bus_type,
                'selected_operator': operator_name,
            })
        else:
            context.update({'error': 'No available Bus Schedule for entered Route and Date'})
            return render(request, 'base.html', context)

    return render(request, 'base.html', context)

def seat_selection(request,schedule_id):
    # print("DEBUG request.GET:", request.GET)
    # print("DEBUG request.POST:", request.POST)
    selected_bus = Schedule.objects.get(id=schedule_id)
    # source = request.GET.get('from')
    # dest = request.GET.get('to')
    # date = request.GET.get('departure_date')
    seats = request.GET.get('number_of_seats')
    # print("DEBUG seats (raw):", seats)
    seats = int(seats)
    total_price=Decimal(seats)*selected_bus.price
    print(total_price)
    context={
        'selected_bus':selected_bus,
        'origin':selected_bus.route.origin,
        'destination':selected_bus.route.destination,
        'date':selected_bus.date,
        'seats':seats,
        'total_price':total_price,
        'schedule_id':selected_bus.id,
    }
    return render(request, 'seat_selection.html',context)

#
# @login_required
# def submit_seats(request, schedule_id):
#     # 1️⃣ Get the schedule
#     selected_bus = Schedule.objects.get(id=schedule_id)
#
#     # 2️⃣ Get seats from POST or GET (depending on how you passed it)
#     selected_seats = request.POST.get('selected_seats') or request.GET.get('selected_seats')
#
#     # 3️⃣ Count number of seats (assuming comma-separated or space-separated)
#     number_of_seats = len(selected_seats.split(','))  # adjust if your format is different
#
#     # 4️⃣ Calculate total price
#     total_price = Decimal(number_of_seats) * selected_bus.price
#
#     # Extract the required details for the template
#     bus_name = selected_bus.bus.license_no
#     departure_date = selected_bus.date
#     departure_time = selected_bus.time
#     origin = selected_bus.route.origin
#     destination = selected_bus.route.destination
#
#     # 5️⃣ Pass to template
#     context = {
#         'selected_bus': selected_bus,
#         'bus_name':bus_name,
#         'departure_date':departure_date,
#         'departure_time':departure_time,
#         'origin': origin,
#         'destination': destination,
#         'selected_seats': selected_seats,
#         'number_of_seats': number_of_seats,
#         'total_price': total_price,
#         'user_id':request.user.user_id ,
#         'user_name':request.user.name,
#     }
#     return render(request, 'payment.html', context)
# def bookings(request):
#     return render(request,'see_bookings.html')
#

# submit seat by sdwp
@login_required
def submit_seats(request, schedule_id):
    if request.method != 'POST':
        return redirect('home')

    selected_bus = get_object_or_404(Schedule, id=schedule_id)
    selected_seats_str = request.POST.get('selected_seats')



    if not selected_seats_str:
        return render(request, 'error_page.html', {'message': 'No seats selected.'})

    selected_seats_list = selected_seats_str.split(',')
    number_of_seats = len(selected_seats_list)
    total_price = Decimal(number_of_seats) * selected_bus.price

    context = {
        'schedule_id' : schedule_id,
        'selected_bus': selected_bus,
        'bus_name':selected_bus.bus.license_no,
        'departure_date':selected_bus.date,
        'departure_time':selected_bus.time,
        'origin': selected_bus.route.origin,
        'destination': selected_bus.route.destination,
        'selected_seats': selected_seats_str,
        'number_of_seats': number_of_seats,
        'total_price': total_price,
        'user_id':request.user.user_id ,
        'user_name':request.user.name,
    }
    for key, value in context.items():
        print(f"Key: {key}, Value: {value}")
    print("--- End Debugging ---")
    return render(request, 'payment.html', context)


# In your views.py file
# SESSION_SELECTED_SEATS_KEY = 'pending_selected_seats'
# SESSION_SCHEDULE_ID_KEY = 'pending_schedule_id'
#
#
# def submit_seats(request, schedule_id):
#     # This view's only job is to handle the form submission and redirect
#     if request.method == 'POST':
#         selected_seats_str = request.POST.get('selected_seats')
#
#         if selected_seats_str:
#             # Save the data to the session
#             request.session[SESSION_SELECTED_SEATS_KEY] = selected_seats_str
#             request.session[SESSION_SCHEDULE_ID_KEY] = schedule_id
#             request.session.modified = True
#
#             # Redirect to the new, login-required view.
#             return redirect('process_booking')
#
#     # If not a POST request, redirect back to the home page
#     messages.error(request, "Invalid request to submit seats.")
#     return redirect('home')
#
# def submit_seats(request, schedule_id):
#     if request.method == "POST":
#         selected_seats = request.POST.get("selected_seats")
#
#         # If no seat selected, go back to seat selection
#         if not selected_seats:
#             return redirect('seat_selection', schedule_id=schedule_id)
#
#         schedule = get_object_or_404(Schedule, id=schedule_id)
#         price = schedule.price
#
#         # Count seats (split by comma) safely
#         seat_list = [seat for seat in selected_seats.split(',') if seat.strip()]
#         total_seat = len(seat_list)
#
#         total_amount = total_seat * price
#
#         # Store in session for payment page
#         request.session['selected_seats'] = selected_seats
#         request.session['total_amount'] = str(total_amount)
#         request.session['total_seat'] = total_seat
#
#         return redirect('process_payment', schedule_id=schedule_id)
#
#     # if user tries to open /submit/ without POST → redirect back
#     return redirect('seat_selection', schedule_id=schedule_id)



# @login_required
# def process_payment(request,schedule_id):
#     if request.method != 'POST':
#         messages.error(request, 'Invalid request to process payment. Please use the booking flow.')
#         return redirect('home')
#
#     schedule_id = request.POST.get('schedule_id')
#     selected_seats_str = request.POST.get('selected_seats')
#     total_price_str = request.POST.get('total_price')
#     payment_method_value = request.POST.get('payment_method')
#
#     # Basic validation
#     if not all([schedule_id, selected_seats_str, total_price_str, payment_method_value]):
#         messages.error(request, "Missing payment details. Please go back and try again.")
#         return redirect('home')
#
#     try:
#         with transaction.atomic():
#             # Lock schedule
#             selected_bus_schedule = Schedule.objects.select_for_update().get(id=schedule_id, del_flag=0)
#             current_user = request.user
#
#             total_price_decimal = Decimal(total_price_str)
#             selected_seats_list = selected_seats_str.split(',')
#             number_of_seats = len(selected_seats_list)
#
#             # Create booking first
#             booking = Booking.objects.create(
#                 schedule=selected_bus_schedule,
#                 customer=current_user,
#                 seat_numbers=selected_seats_str,
#             )
#
#             # Lock and update seat status
#             for seat_no in selected_seats_list:
#                 seat_status_obj = Seat_Status.objects.select_for_update().get(
#                     schedule=selected_bus_schedule,
#                     seat_no=seat_no,
#                     seat_status='Available'
#                 )
#                 seat_status_obj.seat_status = 'Unavailable'
#                 seat_status_obj.booking = booking
#                 seat_status_obj.save()
#
#             # Create ticket
#             ticket = Ticket.objects.create(
#                 booking=booking,
#                 total_seat=number_of_seats,
#                 total_amount=total_price_decimal,
#             )
#
#             # Handle payment method
#             payment_method_code = ''
#             if payment_method_value == 'kpay':
#                 payment_method_code = 'KP'
#             elif payment_method_value == 'wave_money':
#                 payment_method_code = 'WP'
#
#             if payment_method_code:
#                 Payment.objects.create(
#                     ticket=ticket,
#                     payment_method=payment_method_code,
#                 )
#                 messages.success(request, "Payment processed successfully and booking confirmed!")
#             else:
#                 messages.warning(request, "Booking saved, but payment method not recognized. Please verify manually.")
#
#             return redirect('booking_confirmation', booking_id=booking.id)
#
#     except Schedule.DoesNotExist:
#         messages.error(request, "Selected bus schedule not found or is no longer available.")
#         return redirect('home')
#     except Seat_Status.DoesNotExist:
#         messages.error(request, "One or more selected seats are no longer available. Please re-select your seats.")
#         return redirect('seat_selection', schedule_id=schedule_id)
#     except ValueError as e:
#         messages.error(request, f"Invalid data format: {e}. Please try again.")
#         return redirect('home')
#     except Exception as e:
#         messages.error(request, "Unexpected error occurred during booking. Please try again.")
#         print(f"Unhandled exception in process_payment: {e}")
#         return redirect('home')

# new function
# process payment by lls
# @login_required
# def process_payment(request,user_id):
#     if request.method != 'POST':
#         messages.error(request,'Invalid request to process payment. Please use the booking flow.')
#         return redirect('/')
#     schedule_id = request.POST.get('schedule_id')
#     selected_seats_str = request.POST.get('selected_seats')
#     total_price_str = request.POST.get('total_price')
#     payment_method_value = request.POST.get('payment_method')
#
#     # Basic validation for essential data before proceeding
#     if not all([schedule_id, selected_seats_str, total_price_str, payment_method_value]):
#         messages.error(request, "Missing payment details. Please go back and try again.")
#         # Redirect back to the payment page or seat selection if data is incomplete
#         return redirect('/')  # You'll need to define 'some_seat_selection_page' URL
#
#     try:
#         # Use a database transaction for atomicity:
#         # All operations inside this block (getting schedule, updating seats, creating booking/ticket/payment)
#         # will either completely succeed or completely fail. This prevents partial bookings.
#         with transaction.atomic():
#             # Retrieve the Schedule object, and lock it with select_for_update()
#             # to prevent race conditions during seat selection/booking.
#             selected_bus_schedule = Schedule.objects.select_for_update().get(id=schedule_id, del_flag=0)
#             current_user = request.user  # The user is guaranteed to be authentic
#
#             total_price_decimal = Decimal(total_price_str)
#             selected_seats_list = selected_seats_str.split(',')
#             number_of_seats = len(selected_seats_list)
#             payment_method_code = ''
#             if payment_method_value == 'kpay':
#                 payment_method_code = 'KP'
#             elif payment_method_value == 'wave_money':
#                 payment_method_code = 'WP'
#
# #            update seat status for each selected seat
#             for seat_no in selected_seats_list:
#                 # Use select_for_update() to lock the seat row during update
#                 # Crucially, check if the seat is still 'Available' before updating.
#                 seat_status_obj = Seat_Status.objects.select_for_update().get(
#                     schedule=selected_bus_schedule,
#                     seat_no=seat_no,
#                     seat_status='Available'  # Important: This prevents double booking!
#                 )
#                 seat_status_obj.seat_status = 'Unavailable'
#                 seat_status_obj.booking = None  # Initially set to None, will link to booking after creation
#                 # No, you should link it to the booking object *after* the booking is created
#                 seat_status_obj.save()
#             booking = Booking.objects.create(
#                     schedule=selected_bus_schedule,
#                     customer=current_user,
#                     seat_numbers=selected_seats_str,
#             )
#             for seat_no in selected_seats_list:
#                 seat_status_obj = Seat_Status.objects.get(
#                     schedule = selected_bus_schedule,
#                     seat_no = seat_no,
#                 )
#                 seat_status_obj.booking=booking
#                 seat_status_obj.save()
#             ticket = Ticket.objects.create(
#                     booking=booking,
#                     total_seat=number_of_seats,
#                     total_amount=total_price_decimal,
#             )
#             if payment_method_code:
#                 Payment.objects.create(
#                     ticket=ticket,
#                     payment_method=payment_method_code,
#                 )
#             else:
#                 messages.warning(request,"Warning: Payment method not recognized or missing.")
#             messages.success(request,f"Payment method not recognized. Booking recorded, but please verify payment.")
#
#             return redirect('booking_confirmation',booking_id=booking.id)
#             # return redirect('booking_confirmation', booking_id=booking.id)
# #
#     except Schedule.DoesNotExist:
#         messages.error(request, "Selected bus schedule not found or is no longer available.")
#         return redirect('home') # Redirect to home on error
#     except Seat_Status.DoesNotExist: # This means a selected seat was already taken
#         messages.error(request, "One or more selected seats are no longer available. Please re-select your seats.")
#         return redirect('home') # Redirect to home on error
#     except User.DoesNotExist:
#         messages.error(request, "User not logged in or invalid user. Please log in to complete booking.")
#         return redirect('login') # Redirect to login on error
#     except ValueError as e:
#         messages.error(request, f"Invalid data format received: {e}. Please try again.")
#         print(f"ValueError in process_payment: {e}") # For server-side debugging
#         return redirect('home') # Redirect to home on error
#     except Exception as e:
#         messages.error(request, "An unexpected error occurred during booking. Please try again.")
#         print(f"Unhandled exception in process_payment: {e}") # For server-side debugging
#         return redirect('home') # Redirect to home on error


# process payment by sdwp
@login_required
def process_payment(request, user_id):
    if request.method != 'POST':
        messages.error(request, 'Invalid request method.')
        return redirect('home')

    schedule_id = request.POST.get('schedule_id')
    selected_seats_str = request.POST.get('selected_seats', '')
    total_price_str = request.POST.get('total_price')
    payment_method_value = request.POST.get('payment_method')
    # selected_seats_list = selected_seats_str.split(',')

    # Add this print statement to see what you are receiving from the form
    print("Received selected_seats_str:", selected_seats_str)

    # Use a more robust way to split and clean the list
    # .strip() removes any leading/trailing whitespace from each seat number
    selected_seats_list = [seat.strip() for seat in selected_seats_str.split(',') if seat.strip()]

    # Check if the list of selected seats is empty after cleaning
    if not selected_seats_list:
        messages.error(request, "Please select at least one seat.")
        return redirect('select_seats', schedule_id=schedule_id)

    print(schedule_id)
    print(selected_seats_str)
    print(total_price_str)
    print(payment_method_value)

    # for seat_no in selected_seats_str:
    #     print(seat_no)


    if not all([schedule_id, selected_seats_str, total_price_str, payment_method_value]):
        messages.error(request, "Missing payment details. Please go back and try again.")
        # You should redirect to the page where the user can re-enter details
        return redirect('home')

    try:
        try:
            total_price_decimal = Decimal(total_price_str)
        except (ValueError, InvalidOperation):
            messages.error(request, "Invalid total price. Please try again.")
            return redirect('submit_seats', schedule_id=schedule_id)

        with transaction.atomic():
            selected_bus_schedule = get_object_or_404(Schedule.objects.select_for_update(), id=schedule_id)

            # The code from here on is the same as your original code
            booking = Booking.objects.create(
                schedule=selected_bus_schedule,
                customer=request.user,
                seat_numbers=selected_seats_str,
            )

            for seat_no in selected_seats_list:
                seat_status_obj = get_object_or_404(
                    Seat_Status.objects.select_for_update(),
                    schedule=selected_bus_schedule,
                    seat_no=seat_no,
                    seat_status='Available'
                )
                seat_status_obj.seat_status = 'Unavailable'
                seat_status_obj.booking = booking
                seat_status_obj.save()

            ticket = Ticket.objects.create(
                booking=booking,
                total_seat=len(selected_seats_list),
                total_amount=Decimal(total_price_str),
            )

            payment_method_code = 'KP' if payment_method_value == 'kpay' else 'WM'
            Payment.objects.create(
                ticket=ticket,
                payment_method=payment_method_code,
            )

            # Success! Redirect to the booking confirmation page.
            return redirect('booking_confirmation', booking_id=booking.id)

    except (Schedule.DoesNotExist, Seat_Status.DoesNotExist) as e:
        # A specific seat or schedule was not found, meaning it's already taken or invalid.
        messages.error(request, "One or more selected seats are no longer available. Please re-select your seats.")
        return redirect('select_seats', schedule_id=schedule_id)  # Redirect the user back to seat selection.

    except Exception as e:
        # Catch any other unexpected, critical errors.

        messages.error(request, "An unexpected error occurred during booking. Please try again.")
        # Print the error for your own debugging
        import traceback
        print("Unhandled exception in process_payment:", e)
        traceback.print_exc()
        return redirect('submit_seats',schedule_id=schedule_id)

# @login_required
# def booking_confirmation(request):
#     # This view should handle GET requests
#     try:
#         # Get the booking object and ensure it belongs to the current user
#         # Use get_object_or_404 to return a 404 page if the booking doesn't exist
#         booking = get_object_or_404(Booking, id=Booking.id, customer=request.user)
#     except Booking.DoesNotExist:
#         return render(request, 'error_page.html', {'message': 'Booking not found.'})
#
#     # Get the related objects using the booking object
#     ticket = Ticket.objects.get(booking=booking)
#     schedule = booking.schedule
#     bus = schedule.bus
#     route = schedule.route
#     booked_seats_status = Seat_Status.objects.filter(booking=booking)
#
#     context = {
#         'booking': booking,
#         'ticket': ticket,
#         'schedule': schedule,
#         'bus': bus,
#         'route': route,
#         'booked_seats_status': booked_seats_status,
#         'user': request.user,
#     }
#
#     return render(request, 'booking_confirmation.html', context)

@login_required
def booking_confirmation(request, booking_id):
    try:
        booking = get_object_or_404(Booking, id=booking_id, customer=request.user)
        ticket = Ticket.objects.get(booking=booking)
        schedule = booking.schedule
        bus = schedule.bus
        route = schedule.route
        booked_seats_status = Seat_Status.objects.filter(booking=booking)

        context = {
            'booking': booking,
            'ticket': ticket,
            'schedule': schedule,
            'bus': bus,
            'route': route,
            'booked_seats_status': booked_seats_status,
            'user': request.user,
        }

        return render(request, 'booking_confirmation.html', context)

    except Booking.DoesNotExist:
        return render(request, 'error.html', {'message': 'Booking not found.'})
    except Ticket.DoesNotExist:
        return render(request, 'error.html', {'message': 'Ticket information missing.'})


# @login_required # Confirm user is still logged in for this sensitive page
# def booking_confirmation(request, booking_id):
#     try:
#         # Get the booking object, ensure it belongs to the current user
#         booking = Booking.objects.get(id=booking_id, customer=request.user)
#         ticket = Ticket.objects.get(booking=booking) # Get the related ticket
#         schedule = booking.schedule # Access the related schedule
#         bus = schedule.bus # Access the related bus
#         route = schedule.route # Access the related route
#
#         # Get the individual Seat_Status objects for this booking
#         booked_seats_status = Seat_Status.objects.filter(booking=booking)
#
#         context = {
#             'booking': booking,
#             'ticket': ticket,
#             'schedule': schedule,
#             'bus': bus,
#             'route': route,
#             'booked_seats_status': booked_seats_status, # List of Seat_Status objects
#             'user': request.user, # Pass the user object explicitly if needed for other details
#         }
#         return render(request, 'booking_confirmation.html', context)
#
#     except Booking.DoesNotExist:
#         messages.error(request, "Booking not found or you do not have permission to view it.")
#         return redirect('home') # Redirect to home if booking not found
#     except Ticket.DoesNotExist:
#         messages.error(request, "Ticket details missing for this booking.")
#         return redirect('home') # Handle missing ticket gracefully
#     except Exception as e:
#         messages.error(request, "An error occurred while loading your booking confirmation.")
#         print(f"Error loading booking confirmation: {e}")
#         return redirect('home')







# old function
# def process_payment(request):
#     if request.method == 'POST':
#         schedule_id = request.POST.get('schedule_id')
#         selected_seats_str = request.POST.get('selected_seats')
#         total_price_str = request.POST.get('total_price')
#         payment_method_value = request.POST.get('payment_method')
#
#         try:
#             # Retrieve the Schedule object, ensuring del_flag is 0 (not deleted)
#             selected_bus_schedule = Schedule.objects.get(id=schedule_id, del_flag=0)
#             current_user = request.user
#
#             total_price_decimal = Decimal(total_price_str)
#             number_of_seats = len(selected_seats_str.split(',')) if selected_seats_str else 0
#
#             # Map the payment_method value from form to the choices defined in Payment model
#             payment_method_code = ''
#             if payment_method_value == 'kpay':
#                 payment_method_code = 'KP'
#             elif payment_method_value == 'wave_money':
#                 payment_method_code = 'WP'
#             # elif payment_method_value == 'credit_card':
#             #     # Assuming 'CC' is a valid choice in your PAYMENT_METHODS if used
#             #     payment_method_code = 'CC'
#
#             booking = Booking.objects.create(
#                 schedule=selected_bus_schedule,
#                 customer=current_user,
#                 seat_numbers=selected_seats_str,
#             )
#
#             ticket = Ticket.objects.create(
#                 booking=booking,
#                 total_seat=number_of_seats,
#                 total_amount=total_price_decimal,
#             )
#
#             if payment_method_code:
#                 Payment.objects.create(
#                     ticket=ticket,
#                     payment_method=payment_method_code,
#                 )
#             else:
#                 print("Warning: Payment method not recognized or missing.")
#
#             return redirect('process_payment', booking_id=booking.id)
#
#         except Schedule.DoesNotExist:
#             error_message = "Selected bus schedule not found or is no longer available."
#             print(f"Error: {error_message}")
#             return render(request, 'error.html', {'message': error_message})
#         except User.DoesNotExist:
#             error_message = "User not logged in or invalid user. Please log in to complete booking."
#             print(f"Error: {error_message}")
#             return render(request, 'error.html', {'message': error_message})
#         except ValueError as e:
#             error_message = f"Invalid data format received (e.g., price): {e}"
#             print(f"Error: {error_message}")
#             return render(request, 'error.html', {'message': error_message})
#         except Exception as e:
#             error_message = f"An unexpected error occurred during booking: {e}"
#             print(f"Error: {error_message}")
#             return render(request, 'error.html', {'message': "Booking failed due to an internal error. Please try again."})
#     else:
#         # This part handles the initial GET request to display the payment.html page
#         schedule_id = request.GET.get('schedule_id')
#         if not schedule_id:
#             return redirect('seat_selection')
#
#         # Retrieve the schedule for GET request, also checking del_flag
#         try:
#             selected_bus_schedule = Schedule.objects.get(id=schedule_id, del_flag=0)
#         except Schedule.DoesNotExist:
#             return render(request, 'error.html', {'message': 'The selected bus schedule is unavailable.'})
#
#         selected_seats = request.GET.get('selected_seats')
#         if not selected_seats:
#             return redirect('seat_selection')
#
#         number_of_seats = len(selected_seats.split(','))
#         total_price = Decimal(number_of_seats) * selected_bus_schedule.price
#
#         context = {
#             'selected_bus': selected_bus_schedule,
#             'bus_name': selected_bus_schedule.bus.license_no,
#             'departure_date': selected_bus_schedule.date,
#             'departure_time': selected_bus_schedule.time,
#             'origin': selected_bus_schedule.route.origin,
#             'destination': selected_bus_schedule.route.destination,
#             'selected_seats': selected_seats,
#             'number_of_seats': number_of_seats,
#             'total_price': total_price
#         }
#         return render(request, 'payment.html', context)

# def user_login(request):
#     if request.method == 'POST':
#         form = CustomUserAuthenticationForm(request=request, data=request.POST)
#
#         if form.is_valid():
#             user = form.get_user()
#
#             if user is not None:
#                 # FIX: Explicitly specify the custom authentication backend for login
#                 login(request, user, backend='myapp.backends.MyCustomAuthBackend')
#                 messages.success(request, 'You have been logged in successfully!')
#
#                 # --- NEW LOGIC: Check for the 'next' parameter ---
#                 next_url = request.GET.get('next')
#                 if next_url:
#                     # If 'next' exists, redirect the user back to that URL
#                     return redirect(next_url)
#                 # --- END NEW LOGIC ---
#
#                 if isinstance(user, Admin):
#                     return redirect('admin_dashboard')
#                 else:
#                     return redirect('logined_user')
#             else:
#                 messages.error(request, 'Invalid email or password. Please try again.')
#     else:
#         form = CustomUserAuthenticationForm(request=request)
#
#     return render(request, 'login.html', {'form': form})



def home(request):
    bookings = Bus.objects.all()
    return render(request,'base.html',{'bookings':bookings})

@login_required # Add this decorator to protect the view
def profile_page(request):
    # Pass the authenticated user object to the template context
    # return render(request, 'profile_page.html', {'user': request.user})
    user = request.user

    if request.method == 'POST':
        form = CustomUserChangeForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            user.refresh_from_db()
            messages.success(request, 'Your profile has been updated successfully!')
            # --- IMPORTANT CHANGE HERE: Re-render the page instead of redirecting ---
            return redirect('/')
        else:
            print("\n--- FORM ERRORS ---")  # Keep this for debugging if issues persist
            print(form.errors)
            print("--- END FORM ERRORS ---\n")
            messages.error(request, 'There was an error updating your profile. Please correct the errors below.')
            return render(request, 'profile_page.html', {'form': form})
            # messages.error(request, 'There was an error updating your profile. Please correct the errors below.')
    else:
        form = CustomUserChangeForm(instance=user)

    return render(request, 'profile_page.html', {'form': form})

# @login_required(login_url='login')
# def seebookings(request):
#     """
#     Displays the booking history for the logged-in user by querying the database.
#     """
#     if request.user.is_authenticated:
#         # Fetch bookings for the current user and pre-fetch related ticket and payment data
#         # 'select_related' is used for OneToOneField or ForeignKey relationships
#         # Prefetch is used if there were ManyToMany relationships
#         # user_bookings = Booking.objects.filter(customer=request.user).order_by('-booked_time').select_related('ticket')
#         try:
#             user_bookings = Booking.objects.filter(customer=request.user).order_by('-booked_time').select_related(
#                 'ticket', 'schedule')
#         except Booking.DoesNotExist:
#             user_bookings = None
#         context = {
#             'bookings': user_bookings,
#             'today': date.today(),
#         }
#         return render(request, 'see_bookings.html', context)
#     else:
#         # This part is handled by the @login_required decorator, but it's good practice
#         return redirect('login')

# custom user register form by sdwp

def seebookings(request, booking_id=None):
    """
    Manages both the list view and the detailed ticket view in a single function.

    If booking_id is provided in the URL, it fetches and displays a specific ticket.
    Otherwise, it fetches and displays a list of all tickets for the logged-in user.
    """
    if booking_id:
        # Show detailed ticket view if booking_id is provided
        try:
            # Fetch the specific Booking object for the logged-in user.
            # Use select_related to efficiently fetch related Schedule, Ticket,
            # and Payment objects in a single database query.
            booking = Booking.objects.get(id=booking_id,customer=request.user)
            # booking = Booking.objects.select_related(
            #     'schedule',             # Selects the Schedule object
            #     'schedule__bus',        # Selects the related Bus object from Schedule
            #     'schedule__route',
            #     'ticket',               # Selects the related Ticket object
            #     'ticket__payment',      # Selects the related Payment object from Ticket
            #     'customer'         # To get customer name/details if needed
            # ).get(
            #     id=booking_id,
            #     customer=request.user  # CRITICAL: Ensures user can only see their own bookings
            # )
        except Booking.DoesNotExist:
            # If the booking is not found or does not belong to the user,
            # display an error message and redirect to the list view.
            messages.error(request, "Ticket not found or you don't have permission to view it.")
            return redirect('seebookings')

        context = {
            'booking': booking  # Pass the single booking object for detailed view
        }
        return render(request, 'see_bookings.html', context)

    else:
        # Show list of all tickets if no booking_id is provided
        try:
            # Fetch all Booking objects for the current user.
            # Use select_related to efficiently fetch related Schedule and Ticket data.
            user_bookings = (Booking.objects.filter(customer=request.user).order_by('-booked_time'))
            # .select_related(
            #     'schedule',
            #     'schedule__bus', # Selects the related Bus object from Schedule for the list view
            #     'schedule__route',  # <--- ADD THIS LINE
            #     'ticket'
            # ))
        except Booking.DoesNotExist:
            # This case might occur if no bookings exist for the user.
            user_bookings = None

        context = {
            'bookings': user_bookings,  # Pass the list of bookings for the list view
            'today': date.today(),  # Useful for future logic like status or actions
        }
        return render(request, 'see_bookings.html', context)
def user_registration(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)

        if form.is_valid():
            user = form.save()
            # FIX: Explicitly specify the custom authentication backend for login
            login(request, user, backend='myapp.backends.MyCustomAuthBackend')
            messages.success(request, 'Account created successfully!')
            return redirect('login')
        else:
            messages.error(request, 'There was an error creating your account. Please check the form.')
    else:
        form = CustomUserCreationForm()
    return render(request, 'user_registration_form.html', {'form': form})

# user login
def user_login(request):
    if request.method == 'POST':
        form = CustomUserAuthenticationForm(request=request, data=request.POST)

        if form.is_valid():
            user = form.get_user()

            if user is not None:
                # FIX: Explicitly specify the custom authentication backend for login
                login(request, user, backend='myapp.backends.MyCustomAuthBackend')
                messages.success(request, 'You have been logged in successfully!')


                if isinstance(user, Admin):
                    return redirect('admin_dashboard')
                else:
                    return redirect('logined_user')
            else:
                messages.error(request, 'Invalid email or password. Please try again.')
    else:
        form = CustomUserAuthenticationForm(request=request)

    return render(request, 'login.html', {'form': form})

@login_required
def logined_user_home(request):
    user_id = request.user.user_id
    context = {
        'user_id': user_id,
        'user_email': request.user.email,
    }
    return render(request, 'register_user/login_user_home.html', context)

def logout_view(request):
    auth_logout(request)  # <-- use Django’s logout, not your view
    storage = messages.get_messages(request)
    list(storage)
    messages.info(request, "You have been logged out")
    return redirect('login')


def forgot_password_view(request):
    """ Renders the forgot password page """
    return render(request, 'forgot_psw.html')

def send_password_reset_email(request):
    """
    Handles the password reset request.
    It takes an email, finds the user, generates a token, and sends an email.
    """
    if request.method == 'POST':
        try:
            # Parse the JSON data sent from the frontend
            data = json.loads(request.body)
            email = data.get('email')
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid request format.'}, status=400)

        # Do not reveal if the email is registered for security reasons
        # We will send a success message regardless of whether the email exists
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return JsonResponse({'message': 'If an account exists with this email, a reset link has been sent.'},
                                status=200)

        # Generate a unique token for the password reset link
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))

        # Build the password reset URL
        current_site = get_current_site(request)
        reset_link = reverse('password_reset_confirm', kwargs={'uidb64': uid, 'token': token})
        reset_url = f"http://{current_site.domain}{reset_link}"

        # Prepare the email content using a template
        email_subject = 'Password Reset Request'
        email_message = render_to_string('password_reset_email.html', {
            'user': user,
            'reset_url': reset_url,
        })

        # Send the email
        send_mail(
            email_subject,
            email_message,
            'noreply@yourdomain.com',  # Replace with your configured sender email
            [user.email],
            fail_silently=False,
        )

        return JsonResponse({'message': 'A password reset link has been sent to your email address.'}, status=200)

    return JsonResponse({'error': 'Invalid request method.'}, status=405)

# login_user_home.html

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





# Admin Dashboard
@staff_member_required
def admin_dashboard(request):
    no_of_users = User.objects.filter(del_flag = 0).count()
    no_of_buses = Bus.objects.filter(del_flag = 0).count()
    no_of_routes = Route.objects.filter(del_flag=0).count()
    no_of_operators = Operator.objects.filter(del_flag=0).count()
    no_of_schedules = Schedule.objects.filter(del_flag=0).count()
    no_of_bookings = Booking.objects.all().count()
    no_of_tickets = Ticket.objects.all().count()

    bus_query = request.GET.get('bus_number', '')
    route_query = request.GET.get('route', '')
    selected_schedule = None
    seat_status_list = []

    if bus_query and route_query:
        try:
            selected_schedule = Schedule.objects.get(
                Q(bus__license_no__iexact=bus_query) &
                (Q(route__origin__iexact=route_query) | Q(route__destination__iexact=route_query))
            )
            seat_status_list = Seat_Status.objects.filter(schedule=selected_schedule).order_by('seat_no')
        except Schedule.DoesNotExist:
            selected_schedule = None
            seat_status_list = []

    return render(request, 'admin/dashboard.html', {
        'no_of_users': no_of_users,
        'no_of_buses': no_of_buses,
        'no_of_routes': no_of_routes,
        'no_of_operators': no_of_operators,
        'no_of_schedules': no_of_schedules,
        'no_of_bookings': no_of_bookings,
        'no_of_tickets': no_of_tickets,
        'bus_query': bus_query,
        'route_query': route_query,
        'selected_schedule': selected_schedule,
        'seat_status_list': seat_status_list
    })


def user_home(request):

    # Start with the base queryset for all users
    users = User.objects.all()

    # Get the filter parameters from the request
    name_query = request.GET.get('name')
    status_query = request.GET.get('status')

    if name_query:
        # Use Q objects for more complex or combined queries if needed,
        # or simply filter by a single field.
        # This will filter based on both first_name and last_name or just name field
        users = users.filter(name__icontains=name_query)

    if status_query:
        if status_query == 'active':
            # Assuming del_flag = 0 means the user is active
            users = users.filter(del_flag=0)
        elif status_query == 'deleted':
            # Assuming any value other than 0 for del_flag means deleted
            users = users.filter(del_flag__gt=0)

    # Sort the users for a consistent display
    users = users.order_by('user_id')

    # Prepare the context to pass to the template
    users = {
        'users': users
    }

    # Render the user_home.html template with the filtered user list
    return render(request, 'admin/user_home.html', users)


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
    return render(request, 'admin/operator_add_form.html', {'form': operator_form})

def update_operator(request, operator_id):
    operator_info = Operator.objects.get(pk=operator_id)
    if request.method == 'POST':
        operator_form = OperatorForm(request.POST, instance=operator_info)
        if operator_form.is_valid():
            operator_form.save()
            return redirect('operator_home')
    else:
        operator_form = OperatorForm(instance=operator_info)
    return render(request, 'admin/operator_update.html', {'operator_form': operator_form})

def delete_operator(request, operator_id):
    operator_info = Operator.objects.get(id=operator_id)
    operator_info.del_flag = 1 if operator_info.del_flag == 0 else 0
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


# Admin Schedule Section
# def schedule_home(request):
#
#     date_query = request.GET.get('date', '')
#     route_query = request.GET.get('route', '')
#
#     schedules = Schedule.objects.all()
#
#     if date_query:
#         schedules = schedules.filter(date__icontains=date_query)
#
#     if route_query:
#         schedules = schedules.filter(
#             Q(route__origin__icontains=route_query) | Q(route__destination__icontains=route_query)
#         )
#
#     schedules = schedules.order_by('-updated_date')
#
#     buses = Bus.objects.all()
#     routes = Route.objects.all()
#
#     context = {
#         'schedules': schedules,
#         'buses': buses,
#         'routes': routes,
#         'date_query': date_query,
#         'route_query': route_query,
#     }
#
#     # Render the schedule_home template with the context
#     return render(request, 'admin/schedule_home.html', context)

def schedule_home(request):

    date_query = request.GET.get('date', '')
    route_query = request.GET.get('route', '')

    # Annotate the queryset to include the available seats count
    # This counts all related Seat_Status objects that have the status 'Available'.
    schedules = Schedule.objects.annotate(
        available_seats_count=Count('seat_status', filter=Q(seat_status__seat_status='Available'))
    )

    if date_query:
        schedules = schedules.filter(date__icontains=date_query)

    if route_query:
        schedules = schedules.filter(
            Q(route__origin__icontains=route_query) | Q(route__destination__icontains=route_query)
        )

    schedules = schedules.order_by('-updated_date')

    buses = Bus.objects.all()
    routes = Route.objects.all()

    context = {
        'schedules': schedules,
        'buses': buses,
        'routes': routes,
        'date_query': date_query,
        'route_query': route_query,
    }

    # Render the schedule_home template with the context
    return render(request, 'admin/schedule_home.html', context)

# def add_schedule(request):
#     if request.method == 'POST':
#         schedule_form = ScheduleForm(request.POST)
#         if schedule_form.is_valid():
#             print("Form is valid! Saving schedule...")
#             new_schedule = schedule_form.save()
#             bus = new_schedule.bus
#             seat_capacity = bus.seat_capacity
#             for seat_no in range(1, seat_capacity + 1):
#                 Seat_Status.objects.create(
#                     schedule=new_schedule,
#                     seat_no=f"{seat_no:02d}"
#
#                 )
#             return redirect('schedule_home')
#         else:
#             # This is the key change to debug the issue
#             print("Form is NOT valid! Errors:", schedule_form.errors)
#     else:
#         schedule_form = ScheduleForm()
#     return render(request, 'admin/schedule_add_form.html', {'form': schedule_form})

def add_schedule(request):
    """
    Handles the form submission for adding a new bus schedule and automatically
    generates alphanumeric seat statuses based on the bus's seat capacity.
    """
    if request.method == 'POST':
        schedule_form = ScheduleForm(request.POST)
        if schedule_form.is_valid():
            print("Form is valid! Saving schedule...")
            new_schedule = schedule_form.save()

            # Retrieve the bus object from the new schedule to get the seat capacity.
            bus = new_schedule.bus
            seat_capacity = bus.seat_capacity

            # Loop through the total number of seats to create a seat for each one.
            # Using i starting from 0, to simplify calculations.
            for i in range(seat_capacity):
                # Calculate the row letter based on a 3-seat-per-row layout.
                # Integer division `//` gives us the row index (0 for 'A', 1 for 'B', etc.).
                row_letter = chr(ord('A') + i // 3)

                # Calculate the seat number within the row using the modulo operator.
                # `i % 3` gives us 0, 1, or 2, so we add 1 to get seat numbers 1, 2, or 3.
                seat_number_in_row = (i % 3) + 1

                # Combine the letter and number to create the final seat name.
                seat_name = f"{row_letter}{seat_number_in_row}"
                # print(seat_name)

                # Create the Seat_Status object for the new schedule.
                # is_available is set to True by default for new seats.
                Seat_Status.objects.create(
                    schedule=new_schedule,
                    seat_no=seat_name
                )

            # Redirect to a success page after creating the schedule and seats.
            return redirect('schedule_home')
        else:
            # Print form errors for debugging if the form is not valid.
            print("Form is NOT valid! Errors:", schedule_form.errors)
    else:
        # For a GET request, create a blank form instance.
        schedule_form = ScheduleForm()

    # Render the form template.
    return render(request, 'admin/schedule_add_form.html', {'form': schedule_form})

def update_schedule(request,schedule_id):
    schedule_info = Schedule.objects.get(id=schedule_id)

    if request.method == 'POST':
        schedule_form = ScheduleForm(request.POST, instance=schedule_info)
        if schedule_form.is_valid():
            schedule_form.save()
            return redirect('schedule_home')
    else:
        schedule_form = ScheduleForm(instance=schedule_info)

    return render(request,'admin/schedule_update.html',{'form':schedule_form})


def delete_schedule(request,schedule_id):
    schedule_info = Schedule.objects.get(id=schedule_id)
    if schedule_info.del_flag == 0:
        schedule_info.del_flag = 1
        schedule_info.save()
    else:
        schedule_info.del_flag = 0
        schedule_info.save()

    return redirect('schedule_home')

# for booking admindashboard
def booking_list(request):

    bookings = Booking.objects.select_related(
        'customer',
        'schedule__bus__operator',
        'schedule__route'
    ).all()

    origin = request.GET.get('origin')
    destination = request.GET.get('destination')
    operator_name = request.GET.get('operator_name')
    license_no = request.GET.get('license')
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')

    filter_query = Q()

    now = timezone.now()

    filter_query &= Q(schedule__date__gt=now.date()) | \
                    (Q(schedule__date=now.date()) & Q(schedule__time__gte=now.time()))

    if origin:
        filter_query &= Q(schedule__route__origin__icontains=origin)

    if destination:
        filter_query &= Q(schedule__route__destination__icontains=destination)

    if operator_name:
        filter_query &= Q(schedule__bus__operator__operator_name__icontains=operator_name)

    if license_no:
        filter_query &= Q(schedule__bus__license_no__icontains=license_no)

    if from_date and to_date:
        filter_query &= Q(booked_time__date__range=[from_date, to_date])

    bookings = bookings.filter(filter_query)

    bookings = bookings.order_by('-booked_time')

    context = {
        'bookings': bookings,
        'request': request
    }

    return render(request, 'admin/booking_list.html', context)

# def booking_create(request):
#     if request.method == "POST":
#         schedule_id = request.POST.get("schedule_id")
#         customer_id = request.POST.get("customer_id")
#         seat_number = request.POST.get("seat_number")
#
#         schedule = get_object_or_404(Schedule, id=schedule_id)
#         customer = get_object_or_404(User, id=customer_id)
#
#         Booking.objects.create(
#             schedule=schedule,
#             customer=customer,
#             seat_number=seat_number,
#             booked_time=timezone.now()
#         )
#         return redirect("booking_list")
#
#     schedules = Schedule.objects.all()
#     customers = User.objects.all()
#     return render(request, "admin/booking_form.html", {
#         "schedules": schedules,
#         "customers": customers
#     })

# for history admindashboard
# def history_view(request):
#     history_records = Booking.objects.all().order_by('-booked_time')
#     # change field as needed
#     return render(request, "admin/history.html", {"history_records": history_records})

def history_list(request):

    bookings = Booking.objects.select_related(
        'customer',
        'schedule__bus__operator',
        'schedule__route'
    ).all()

    origin = request.GET.get('origin')
    destination = request.GET.get('destination')
    operator_name = request.GET.get('operator_name')
    license_no = request.GET.get('license')
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')

    filter_query = Q()

    now = timezone.now()

    filter_query &= Q(schedule__date__lt=now.date()) | \
                    (Q(schedule__date=now.date()) & Q(schedule__time__lt=now.time()))

    # Apply additional filters based on user input from the form
    if origin:
        filter_query &= Q(schedule__route__origin__icontains=origin)

    if destination:
        filter_query &= Q(schedule__route__destination__icontains=destination)

    if operator_name:
        filter_query &= Q(schedule__bus__operator__operator_name__icontains=operator_name)

    if license_no:
        filter_query &= Q(schedule__bus__license_no__icontains=license_no)

    if from_date and to_date:
        # Filter by the booked time date range, if provided
        filter_query &= Q(booked_time__date__range=[from_date, to_date])

    # Apply all filters to the bookings queryset
    history_items = bookings.filter(filter_query)

    # Order the results from most recent to oldest booked time
    history_items = history_items.order_by('-booked_time')

    context = {
        'history': history_items,
        'request': request
    }

    return render(request, 'admin/history.html', context)