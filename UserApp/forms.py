from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django import forms
from .models import UserProfile
from CalendarApp.models import Machine




class SignUpForm(UserCreationForm):
    email = forms.EmailField(label="", widget=forms.TextInput(attrs={'class':'form-control', 'placeholder':'Email Address'}))
    first_name = forms.CharField(label="", max_length=100, widget=forms.TextInput(attrs={'class':'form-control', 'placeholder':'First Name'}))
    last_name = forms.CharField(label="", max_length=100, widget=forms.TextInput(attrs={'class':'form-control', 'placeholder':'Last Name'}))
    group_name = forms.CharField(label="", max_length=100, widget=forms.TextInput(attrs={'class':'form-control', 'placeholder':'Group Name'}))

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
        queryset=Machine.objects.filter(is_open=True),  #Machine.objects.all(),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check'}), #-inline
        required=True  # Set to True if selecting at least one machine is mandatory
    )

    # Field for selecting the preferred machine
    preferred_machine = forms.ModelChoiceField(
        label="Preferred Machine",
        help_text='<span class="form-text text-muted"><small>Choose one preferred machine.</small></span>',
        queryset=Machine.objects.filter(is_open=True), #all(),
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
        
        #now get the UserProfile data
        group_name = self.cleaned_data.get('group_name')
        
        is_external = self.cleaned_data['access_type']=='external'
        print(user.username)
        print('self cleaned: ', self.cleaned_data['access_type'])
        print('is_external: ', is_external)
                
        # Handle the 'machines4ThisUser' field and create the ManyToMany relationship
        selected_machines = self.cleaned_data.get('machines_allowed')

        # Handle the 'machine2Book' field (corrected field name)
        preferred_machine = self.cleaned_data.get('preferred_machine')

        user_profile = UserProfile(user=user, group_name=group_name)
        user_profile.save()
        user_profile.machines4ThisUser.set(selected_machines)
        user_profile.preferred_machine_name = preferred_machine.machine_name
        user_profile.is_external = is_external
        user_profile.save()
        
        return user


    def clean(self):
        print('clean\n')
        cleaned_data = super().clean()
        selected_machines = cleaned_data.get('machines_allowed')
        preferred_machine_name = str(cleaned_data.get('preferred_machine'))

        if preferred_machine_name and selected_machines:
            names = [str(machine.machine_name) for machine in selected_machines]

            if preferred_machine_name not in names:
                self.add_error('preferred_machine', 'Preferred machine must be one of the selected machines.')
        print('cleaned_data')
 
        return cleaned_data




