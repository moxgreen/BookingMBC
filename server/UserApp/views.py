from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .forms import SignUpForm, ChangePwdForm, ChangeServiceForm
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
    template_name = 'password_reset.html'

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
                return render(request, 'password_reset_done.html', {'reset' : True})
            else:
                # Form is invalid, redisplay it with errors
                return render(request, self.template_name, {'form': form, 'uidb64': uidb64, 'token': token})
        else:
            # Token is invalid
            return render(request, self.template_name, {'validlink': False})



######################################################################################
#                                   Password change                                  #
######################################################################################

from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib.auth.views import PasswordChangeView

class CustomPasswordChangeView(LoginRequiredMixin, PasswordChangeView):
    template_name = 'password_change.html'
    form_class = ChangePwdForm
    # if successful call the url password_change/done/
    success_url = reverse_lazy('custom_password_change_done')

 
    def form_invalid(self, form):
        # Check if the form has specific error messages for old_password, new_password1, or new_password2
        old_password_error = form.errors.get('old_password', None)
        new_password1_error = form.errors.get('new_password1', None)
        new_password2_error = form.errors.get('new_password2', None)

        if old_password_error:
            messages.error(self.request, old_password_error.as_text())
        elif new_password1_error:
            messages.error(self.request, new_password1_error.as_text())
        elif new_password2_error:
            messages.error(self.request, new_password2_error.as_text())
        else:
            messages.error(self.request, 'There was an error with the form submission. Please correct the errors.')
        return super().form_invalid(form)

 
class CustomPasswordChangeDoneView(LoginRequiredMixin, View):
    template_name = 'password_reset_done.html'

    def get(self, request, *args, **kwargs):
        # Display the success page
        return render(request, self.template_name, {'reset' : False})    
    

######################################################################################
#                                    Add Service                                     #
######################################################################################

class ServicesChangeView(View):
    template_name = 'services_add.html'
    form_class = ChangeServiceForm
    # if successful call the url password_change/done/
    success_url = reverse_lazy('home')

    def get(self, request, *args, **kwargs):
        form = self.form_class(user=request.user)
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST, user=request.user)

        if form.is_valid():
            form.save(user=request.user)
            # Additional logic if needed
            return redirect(self.success_url)

        return render(request, self.template_name, {'form': form})
