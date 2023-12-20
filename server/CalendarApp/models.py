from django.db import models

class Machine(models.Model):
    machine_name = models.CharField(max_length=50)
    facility = models.CharField(max_length=100)
    is_open = models.BooleanField(default=True, null=True, blank=True)
    hourly_cost = models.DecimalField(max_digits=5, decimal_places=2)
    hourly_cost_assisted = models.DecimalField(max_digits=5, decimal_places=2)
    hourly_cost_external = models.DecimalField(max_digits=5, decimal_places=2)
    hourly_cost_external_assisted = models.DecimalField(max_digits=5, decimal_places=2)
    hourly_cost_buyer = models.DecimalField(default=0, max_digits=5, decimal_places=2, null=True, blank=True )

    def __str__(self):
        return self.machine_name

class Booking(models.Model):
    username = models.CharField(max_length=100)
    title = models.CharField(max_length=100)
    machine_obj = models.ForeignKey(Machine, on_delete=models.DO_NOTHING)
    booked_start_date = models.DateTimeField()
    booked_end_date = models.DateTimeField()
    is_assisted = models.BooleanField(default=True, null=True, blank=True)
    duration = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.username} booked {self.machine_obj.machine_name} from {self.booked_start_date} to {self.booked_end_date}"

