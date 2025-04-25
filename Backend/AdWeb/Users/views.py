from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model
from .forms import RegistrationForm, LoginForm
from .utils import send_verification_email

# Create your views here.
def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_verified = False  # Set to False until verified
            user.save()
            send_verification_email(user)  # Send verification email
            return redirect('registration_sent')  # Redirect to a page informing the user to check their email
    else:
        form = RegistrationForm()
    return render(request, 'register.html', {'form': form})

def login(request):
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if user.is_verified:
                # Log the user in
                login(request, user)
                return redirect('home')  # Redirect to a home page or dashboard
            else:
                form.add_error(None, "Please verify your email before logging in.")
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form})