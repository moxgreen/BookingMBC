from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from django.contrib.auth.models import User
from django import forms
from .models import UserProfile, MBCGroup
from CalendarApp.models import Machine




class SignUpForm(UserCreationForm):
    email = forms.EmailField(label="", widget=forms.TextInput(attrs={'class':'form-control', 'placeholder':'Email Address'}))
    first_name = forms.CharField(label="", max_length=100, widget=forms.TextInput(attrs={'class':'form-control', 'placeholder':'First Name'}))
    last_name = forms.CharField(label="", max_length=100, widget=forms.TextInput(attrs={'class':'form-control', 'placeholder':'Last Name'}))

    # Field for selecting the group
    group_name = forms.ModelChoiceField(
        label="Group Name",
        help_text='<span class="form-text text-muted"><small>Choose one group name.</small></span>',
        queryset=MBCGroup.objects.all().order_by('group_name'), #all(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=True
    )

    # Add the radio button for internal and external options
    INTERNAL = 'internal'
    EXTERNAL = 'external'
    ACCESS_CHOICES = [
        (INTERNAL, 'Internal'),
        (EXTERNAL, 'External'),
    ]
    
    access_type = forms.ChoiceField(
        label="Access Type",
        widget=forms.RadioSelect(attrs={'class': 'form-check-inline'}),
        choices=ACCESS_CHOICES,
        required=True
    )

    #select the machines that can be used
    machines_allowed = forms.ModelMultipleChoiceField(
        label="Select which machines you are allowed to use",  # Add the label here
        #help_text='<span class="form-text text-muted"><small>Choose one or more machines.</small></span>',  # Add help text
        queryset=Machine.objects.filter(is_open=True).order_by('machine_name'),  #Machine.objects.all(),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check form-check-inline', 'id': 'your-checkbox-widget'}), #-inline
        required=True  # Set to True if selecting at least one machine is mandatory
    )

    # Field for selecting the preferred machine
    preferred_machine = forms.ModelChoiceField(
        label="Preferred Machine",
        help_text='<span class="form-text text-muted"><small>Choose one preferred machine.</small></span>',
        queryset=Machine.objects.filter(is_open=True).order_by('machine_name'), #all(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=True
    )

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email',
                  'group_name',
                  'access_type',
                  'password1', 'password2',
                  'machines_allowed', 'preferred_machine')


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        #self.fields['access_type'].initial = self.INTERNAL
        self.empty_permitted = True #prevents showing errors with an empty form


    def save(self, commit=True):
        user = super(SignUpForm, self).save(commit=False)
        user.save()
        
        # Get the UserProfile data
        selected_group = self.cleaned_data.get('group_name')
        # Get the is_external state
        is_external = self.cleaned_data['access_type']=='external'
        # Handle the 'machines4ThisUser' field and create the ManyToMany relationship
        selected_machines = self.cleaned_data.get('machines_allowed')

        # Handle the 'machine2Book' field (corrected field name)
        preferred_machine = self.cleaned_data.get('preferred_machine')

        user_profile = UserProfile(user=user)
        user_profile.save()
        
        user_profile.group = selected_group
        if user_profile.group.location == 'NO MBC':
            is_external = True
        user_profile.machines4ThisUser.set(selected_machines)
        user_profile.preferred_machine_name = preferred_machine.machine_name
        user_profile.is_external = is_external
        user_profile.save()
        
        return user


    def clean(self):
        cleaned_data = super().clean()
        selected_machines = cleaned_data.get('machines_allowed')
        preferred_machine_name = str(cleaned_data.get('preferred_machine'))

        if preferred_machine_name and selected_machines:
            names = [str(machine.machine_name) for machine in selected_machines]

            if preferred_machine_name not in names:
                self.add_error('preferred_machine', 'Preferred machine must be one of the selected machines.')
 
        return cleaned_data



class ChangePwdForm(PasswordChangeForm):
    old_password = forms.CharField(label="Old password:", max_length=100, widget=forms.PasswordInput(attrs={'class':'form-control', 'type':'password'}))
    new_password1 = forms.CharField(label="New password:", max_length=100, widget=forms.PasswordInput(attrs={'class':'form-control', 'type':'password'}))
    new_password2 = forms.CharField(label="New password confirmation:", max_length=100, widget=forms.PasswordInput(attrs={'class':'form-control','type':'password'}))

    class Meta:
        model = User
        fields = ('old_password', 'new_password1', 'new_password2')



class ChangeServiceForm(forms.Form):
    
    #select the machines that can be used
    machines_allowed = forms.ModelMultipleChoiceField(
        label="Add machines you are allowed to use",  # Add the label here
        #help_text='<span class="form-text text-muted"><small>Choose one or more machines.</small></span>',  # Add help text
        queryset=None, #Machine.objects.filter(is_open=True),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check form-check-inline', 'id': 'your-checkbox-widget'}), #-inline
        required=False  # Set to True if selecting at least one machine is mandatory
    )

    # Field for selecting the preferred machine
    preferred_machine = forms.ModelChoiceField(
        label='', #"Do you need to change the Preferred Machine?",
        help_text='<span class="form-text text-muted"><small>Choose one preferred machine.</small></span>',
        queryset=None, #Machine.objects.filter(is_open=True).order_by('machine_name'), #all(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=False
    )

    class Meta:
        model = User
        fields = ('machines_allowed', 'preferred_machine')


    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_profile = UserProfile.objects.get(user=user)
        # Adjust the queryset based on the user's allowed machines
        allowed_machines = self.user_profile.machines4ThisUser.all()
        #select open machines - machiene4ThisUser 
        self.fields['machines_allowed'].queryset = Machine.objects.filter(is_open=True)\
                                .exclude(id__in=allowed_machines).order_by('machine_name')
        self.fields['preferred_machine'].queryset = Machine.objects.filter(is_open=True)\
                                .order_by('machine_name')
        lbl = 'Your preferred service is: \"' + self.user_profile.preferred_machine_name +'\". Select a name in the list to change it:'
        self.fields['preferred_machine'].label = lbl

 
    def save(self, user):
        # Get the existing UserProfile instance associated with the user
        user_profile = self.user_profile

        # Handle the 'machines4ThisUser' field and create the ManyToMany relationship
        selected_machines = self.cleaned_data.get('machines_allowed')

        # Handle the 'machine2Book' field (corrected field name)
        preferred_machine = self.cleaned_data.get('preferred_machine')
 
        if (selected_machines != None) : user_profile.machines4ThisUser.add(*selected_machines)
        if (preferred_machine != None) : user_profile.preferred_machine_name = preferred_machine.machine_name
        user_profile.save()
        
        return user_profile


    def clean(self):
        cleaned_data = super().clean()
        selected_machines = cleaned_data.get('machines_allowed')
        preferred_machine_name = cleaned_data.get('preferred_machine')

        if ((preferred_machine_name != None) and (selected_machines != None)):
            #the choice is between previously selected machines and machines selected in this form
            oldnames = [str(machine.machine_name) for machine in self.user_profile.machines4ThisUser.all()]
            newnames = [str(machine.machine_name) for machine in selected_machines]
            allnames = oldnames + newnames

            if str(preferred_machine_name) not in allnames:
                self.add_error('preferred_machine', 'Preferred machine must be either a previously allowed machine or one of the selected machines.')
        else:
            print('preferred machine NOT changed')
        return cleaned_data
