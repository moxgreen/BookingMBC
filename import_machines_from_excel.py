# -*- coding: utf-8 -*-
# populate_database.py

# populate_database.py

import os
import sys
import pandas as pd
from django.db import IntegrityError

# Set the Django project settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "BookingMBC.settings")

# Add the project root directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import django
django.setup()

from CalendarApp.models import Machine  # Adjust the import path based on your project structure

def populate_database(excel_file_path):
    # Read the Excel file into a pandas DataFrame
    df = pd.read_excel(excel_file_path)
    df = df.fillna(0) #fill NaN of excel empty cells with value of 0
    
    # Define a mapping for the 'is_open' field
    is_open_mapping = {'open': True, 'restricted': False}

    # Iterate through the DataFrame rows
    for index, row in df.iterrows():
        try:
            # Try to get the existing record or create a new one
            machine, created = Machine.objects.get_or_create(
                machine_name=row['machine_name'],
                defaults={
                    'facility': row['facility'],
                    'hourly_cost': row['hourly_cost'],
                    'hourly_cost_assisted': row['hourly_cost_assisted'],
                    'hourly_cost_external': row['hourly_cost_external'],
                    'hourly_cost_external_assisted': row['hourly_cost_external_assisted'],
                    'is_open': is_open_mapping.get(row['is_open'].lower(), True),  # Use the mapping
                }
            )

            if not created:
                # Update the existing record if it already exists
                machine.facility = row['facility']
                machine.hourly_cost = row['hourly_cost']
                machine.hourly_cost_assisted = row['hourly_cost_assisted']
                machine.hourly_cost_external = row['hourly_cost_external']
                machine.hourly_cost_external_assisted = row['hourly_cost_external_assisted']
                machine.is_open = is_open_mapping.get(row['is_open'].lower(), True)  # Use the mapping
                machine.save()
        except IntegrityError as e:
            print(f"Error processing row {index + 1}: {e}")


if __name__ == "__main__":
    # Assuming the script is in the root directory of your project
    excel_file_path = "machines.xlsx"
    populate_database(excel_file_path)


