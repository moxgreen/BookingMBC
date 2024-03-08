from django.db import models

class Machine(models.Model):
    machine_name = models.CharField(max_length=50)
    facility = models.CharField(max_length=100)
    is_open = models.BooleanField(default=True, null=True, blank=True)
    max_booking_duration = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    hourly_cost = models.DecimalField(max_digits=5, decimal_places=2, null=False, blank=False, default=0)
    hourly_cost_assisted = models.DecimalField(max_digits=5, decimal_places=2, null=False, blank=False, default=0)
    hourly_cost_external = models.DecimalField(max_digits=5, decimal_places=2, null=False, blank=False, default=0)
    hourly_cost_external_assisted = models.DecimalField(max_digits=5, decimal_places=2, null=False, blank=False, default=0)
    hourly_cost_buyer = models.DecimalField(max_digits=5, decimal_places=2, null=False, blank=False, default=0)
    hourly_cost_buyer_assisted = models.DecimalField(max_digits=5, decimal_places=2, null=False, blank=False, default=0)

    def __str__(self):
        return self.machine_name

class Booking(models.Model):
    username = models.CharField(max_length=100)
    title = models.CharField(max_length=100)
    machine_obj = models.ForeignKey(Machine, on_delete=models.CASCADE)
    booked_start_date = models.DateTimeField()
    booked_end_date = models.DateTimeField()
    is_assisted = models.BooleanField(default=True, null=True, blank=True)
    duration = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.username} booked {self.machine_obj.machine_name} from {self.booked_start_date} to {self.booked_end_date}"

