from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .forms import SignUpForm
from .models import UserProfile


def home(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('CalendarApp:calendar_view')
        else:
            messages.error(request, "There Was An Error Logging In, Please Try Again...")
            return redirect('home')
    else :
        if not (request.user.is_anonymous) :
            #print("an authenticated user requests the home page")
            return redirect('CalendarApp:calendar_view')
        else:
            context={}        
            #print("we need authentication: go to login")
            return render(request, 'home.html', context) #accessing a protected html page triggers login

def logout_user(request):
	logout(request)
	messages.success(request, "You Have Been Logged Out...")
	return redirect('home')


def register_user(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
			# Authenticate and login
            username = form.cleaned_data['username']
            password = form.cleaned_data['password1']
            user = authenticate(username=username, password=password)
            login(request, user)

            #messages.success(request, "You Have Successfully Registered! Welcome!")
            return redirect('home')
    else:
        form = SignUpForm(request.POST)

    return render(request, 'register.html', {'form':form})


def reports(request):
    return redirect('CalendarApp:reports_view')

######################################################################################
#                                    Password reset                                  #
######################################################################################

from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.views import View
from django.http import Http404
from django.contrib.auth.forms import SetPasswordForm

class CustomPasswordResetView(View):
    template_name = 'reset_pwd.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)

    def post(self, request, *args, **kwargs):
        usn = request.POST.get('username')
        email = request.POST.get('email')

        try:
            #we use the UserProfile because it holds the token field
            up = UserProfile.objects.get(user__email=email)
            if usn != up.user.username: raise UserProfile.DoesNotExist()
            
            # Generate a one-time token and save it in the user's profile
            token = default_token_generator.make_token(up.user)
            up.password_reset_token = token
            up.save()

            # Redirect to the password reset confirmation view with the user's ID and token
            return redirect('custom_password_reset_confirm', uidb64=up.user.pk, token=token)
        
        except UserProfile.DoesNotExist:
            # Handle the case when no user is found (you may want to display an error message)
            messages.error(request, "User with this username or email address not found.")
            return render(request, self.template_name)
        
        

class CustomPasswordResetConfirmView(View):
    template_name = 'password_reset_confirm.html'
    form_class = SetPasswordForm

    def get_user(self, uidb64):
        #request access to users. Easier than with UserProfile
        user_model = get_user_model()
        try:
            return user_model.objects.get(pk=uidb64)
        except user_model.DoesNotExist:
            raise Http404

    def get(self, request, uidb64, token, *args, **kwargs):
        user = self.get_user(uidb64)
        
        # Check if the token is valid
        if default_token_generator.check_token(user, token):
            # Display the password reset form
            form = self.form_class(user=user)
            return render(request, self.template_name, {'form': form, 'uidb64': uidb64, 'token': token})
        else:
            # Token is invalid
            return render(request, self.template_name, {'validlink': False})

    def post(self, request, uidb64, token, *args, **kwargs):
        user = self.get_user(uidb64)

        # Check if the token is valid
        if default_token_generator.check_token(user, token):
            form = self.form_class(user, request.POST)
            if form.is_valid():
                # Set the new password
                form.save()
                return render(request, 'password_reset_complete.html')
            else:
                # Form is invalid, redisplay it with errors
                return render(request, self.template_name, {'form': form, 'uidb64': uidb64, 'token': token})
        else:
            # Token is invalid
            return render(request, self.template_name, {'validlink': False})
