from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from django.db import models
from CalendarApp.models import Machine

from django.db.models import Q


class MBCGroup(models.Model):
    ####################################################################
    # groups need to be loaded by a script before registering any user #
    ####################################################################
    
    group_name = models.CharField(max_length=100, null=True, blank=True)
    machines_bought = models.ManyToManyField(Machine, related_name='machines_bought', blank=True)

    MBC_CHOICES = [
        ('MBC1', 'MBC1'),
        ('MBC2', 'MBC2'),
        ('NO_MBC', 'NO_MBC'),
    ]
    location = models.CharField(max_length=6, choices=MBC_CHOICES, default='NO_MBC', null=True, blank=True)

    def __str__(self):
        return self.group_name
    

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    group = models.ForeignKey(MBCGroup, null=True, on_delete=models.SET_NULL)
    machines4ThisUser = models.ManyToManyField(Machine, related_name='machines4ThisUser', blank=True)
    preferred_machine_name =  models.CharField(max_length=50)
    is_external = models.BooleanField(default=True, null=True, blank=True)
    
    password_reset_token = models.CharField(max_length=100, null=True, blank=True)
    
    def __str__(self):
        return self.user.username
    
    


#@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created and instance.is_superuser:
        # Create a UserProfile instance when a superuser is created
        ######################################################################
        # I need to always have Machines loaded first and with Elyra and DM6 #
        ######################################################################
        
        u=UserProfile.objects.create( user=instance,
                                      group_name='Staff',
                                      preferred_machine_name='Elyra',
                                    )
        machines_queryset = Machine.objects.filter(Q(machine_name='Elyra') | Q(machine_name='DM6'))
        u.machines4ThisUser.set(machines_queryset)


#@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
     # Save the UserProfile whenever the associated User is saved
    if instance.is_superuser:
        try:
            profile = UserProfile.objects.get(user=instance)
            profile.save()
        except UserProfile.DoesNotExist:
            # If UserProfile doesn't exist, create it
            print('unexpected missing User Profile: create a new one')
            UserProfile.objects.create(user=instance, group_name='Staff', preferred_machine_name='Elyra')
