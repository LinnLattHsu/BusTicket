from cProfile import label

from django import forms
from django.contrib.auth import (
    authenticate,
    get_user_model

)
from .models import Operator
from .models import Bus
User = get_user_model()

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
    email = forms.EmailField(label='Email address')
    email2 = forms.EmailField(label='Confirm Email')
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = [
            'username',
            'email',
            'email2',
            'password'
        ]

    def clean(self, *args, **kwargs):
        email = self.cleaned_data.get('email')
        email2 = self.cleaned_data.get('email2')
        if email != email2:
            raise forms.ValidationError("Emails must match")
        email_qs = User.objects.filter(email=email)
        if email_qs.exists():
            raise forms.ValidationError(
                "This email has already been registered")
        return super(UserRegisterForm, self).clean(*args, **kwargs)
