from cProfile import label

from django import forms
from django.contrib.auth import (
    authenticate,
    get_user_model

)
from django.contrib.auth.hashers import make_password
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import User
from .models import Operator
from .models import Bus
from .models import Route
from .models import Schedule
User = get_user_model()

# for operator form
class OperatorForm(forms.ModelForm):
    class Meta:
        model = Operator
        fields = ['operator_name']

        widgets = {
            'operator_name': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm p-2',
                'placeholder': 'Enter operator name'
            }),
        }

# for route form
class RouteForm(forms.ModelForm):
    class Meta:
        model = Route
        fields = ['origin','destination']

        widgets = {
            'origin': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm p-2',
                'placeholder': 'Enter origin city'
            }),
            'destination': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm p-2',
                'placeholder': 'Enter destination city'
            }),
        }

# for bus form
class BusForm(forms.ModelForm):
    class Meta:
        model = Bus
        fields = ['license_no', 'seat_capacity', 'bus_type', 'operator']
        widgets = {
            'license_no': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm p-2',
                'placeholder': 'Enter bus license number'
            }),
            'seat_capacity': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm p-2',
                'placeholder': 'Enter bus seat capacity'
            }),
            'bus_type': forms.Select(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm p-2'
            }),
            'operator': forms.Select(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm p-2'
            }),
        }

# for schedule form
class ScheduleForm(forms.ModelForm):
    class Meta:
        model = Schedule
        fields = ['bus', 'route', 'date', 'time', 'price']
        widgets = {
            'bus': forms.Select(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm p-2'
            }),
            'route': forms.Select(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm p-2'
            }),
            'date': forms.DateInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm p-2',
                'type': 'date'  # This ensures the date picker widget is used in HTML
            }),
            'time': forms.TimeInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm p-2',
                'type': 'time'  # This ensures the time picker widget is used in HTML
            }),
            'price': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm p-2',
                'placeholder': 'Enter ticket price'
            }),
        }
class BookingForm(forms.Form):
    model = Bus
    source = forms.Select(attrs={'class':'form-select'})
    dest = forms.Select(attrs={'class': 'form-select'})
    departure_date = forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    number_of_seats = forms.NumberInput(attrs={'class': 'form-control'})

class UserLoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)

    def clean(self, *args, **kwargs):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if username and password:
            user = authenticate(username=username, password=password)
            if not user:
                raise forms.ValidationError('This user does not exist')
            if not user.check_password(password):
                raise forms.ValidationError('Incorrect password')
            if not user.is_active:
                raise forms.ValidationError('This user is not active')
        return super(UserLoginForm, self).clean(*args, **kwargs)

class PaymentForm(forms.Form):
    name = forms.CharField(max_length=100, required=True)
    email = forms.EmailField(required=True)
    card_number = forms.CharField(max_length=19, required=True)  # Format: xxxx-xxxx-xxxx-xxxx
    expiry_date = forms.CharField(max_length=5, required=True)  # Format: MM/YY
    cvv = forms.CharField(max_length=3, required=True, widget=forms.PasswordInput)
    insurance = forms.BooleanField(required=False)  # Optional field for insurance

class UserRegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['name', 'email', 'password', 'nrc', 'address', 'phone_no']



# for user_register form by sdwp

    """
    A custom form for creating new users. It extends Django's
    built-in UserCreationForm and adds the extra fields from our
    custom User model with specific styling.
    """

class CustomUserCreationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-input'}))
    password2 = forms.CharField(label='Password confirmation',
                                widget=forms.PasswordInput(attrs={'class': 'form-input'}))

    class Meta:
        """
        The Meta class configures the form to use our custom User model
        and includes a widgets dictionary for custom styling.
        """
        model = User
        fields = (
            'name',
            'email',
            'nrc',
            'address',
            'phone_no',
            # Do not include 'password' here as it's handled separately
        )

        # Add a widgets dictionary to apply custom HTML attributes to the model fields
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input'}),
            'email': forms.EmailInput(attrs={'class': 'form-input'}),
            'nrc': forms.TextInput(attrs={'class': 'form-input'}),
            'address': forms.TextInput(attrs={'class': 'form-input'}),
            'phone_no': forms.TextInput(attrs={'class': 'form-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ensure password field is not rendered twice
        self.fields['password'].required = True
        self.fields['password2'].required = True

    def clean_password2(self):
        """
        This custom cleaning method checks if the passwords match.
        """
        password = self.cleaned_data.get('password')
        password2 = self.cleaned_data.get('password2')
        if password and password2 and password != password2:
            raise forms.ValidationError("Passwords don't match.")
        return password2

    def save(self, commit=True):
        """
        This method saves the user to the database with a hashed password.
        """
        user = super().save(commit=False)
        # Hash the password before saving
        user.password = make_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user


class CustomUserAuthenticationForm(forms.Form):
    """
    A custom authentication form that uses email instead of username.
    """
    username = forms.CharField(label='Email', max_length=150)
    password = forms.CharField(label='Password', widget=forms.PasswordInput)

    def __init__(self, request=None, *args, **kwargs):
        """
        The 'request' is passed as a keyword argument to make sure the
        authentication backend can use it.
        """
        self.request = request
        self.user_cache = None
        super().__init__(*args, **kwargs)

    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if username and password:
            # Pass the request as a keyword argument to authenticate
            self.user_cache = authenticate(request=self.request, username=username, password=password)
            if self.user_cache is None:
                raise forms.ValidationError(
                    "Invalid email or password. Please try again.",
                    code='invalid_login',
                )
        return self.cleaned_data

    def get_user(self):
        return self.user_cache

# class UserRegisterForm(forms.ModelForm):
#     email = forms.EmailField(label='Email address')
#     email2 = forms.EmailField(label='Confirm Email')
#     password = forms.CharField(widget=forms.PasswordInput)
#
#     class Meta:
#         model = User
#         fields = [
#             'username',
#             'email',
#             'email2',
#             'password'
#         ]
#
#     def clean(self, *args, **kwargs):
#         email = self.cleaned_data.get('email')
#         email2 = self.cleaned_data.get('email2')
#         if email != email2:
#             raise forms.ValidationError("Emails must match")
#         email_qs = User.objects.filter(email=email)
#         if email_qs.exists():
#             raise forms.ValidationError(
#                 "This email has already been registered")
#         return super(UserRegisterForm, self).clean(*args, **kwargs)

class CustomUserChangeForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['name', 'nrc', 'address', 'phone_no'] # Specify the fields you want users to be able to edit

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make the email field readonly as it's typically the USERNAME_FIELD
        # and not intended to be changed directly via a profile update form
        if 'email' in self.fields: # Check if 'email' field exists (it should, from AbstractBaseUser)
            self.fields['email'].widget.attrs['readonly'] = True
            self.fields['email'].required = False # Not required for update if read-only

        # Apply Bootstrap's 'form-control' class for consistent styling
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'

        # Optional: Apply specific Bootstrap classes for larger, rounded inputs
        self.fields['name'].widget.attrs['class'] += ' form-control-lg rounded-pill custom-input'
        if 'nrc' in self.fields:
            self.fields['nrc'].widget.attrs['class'] += ' form-control-lg rounded-pill custom-input'
        if 'address' in self.fields:
            self.fields['address'].widget.attrs['class'] += ' form-control-lg rounded-3 custom-textarea'
        if 'phone_no' in self.fields:
            self.fields['phone_no'].widget.attrs['class'] += ' form-control-lg rounded-pill custom-input'
        if 'email' in self.fields: # Apply styling to readonly email field as well
            self.fields['email'].widget.attrs['class'] += ' form-control-lg rounded-pill custom-input bg-light'
