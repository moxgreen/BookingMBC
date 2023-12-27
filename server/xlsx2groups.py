# -*- coding: utf-8 -*-
# populate_database.py

import os
import sys
import pandas as pd
import re
from django.db import IntegrityError

# Set the Django project settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "BookingMBC.settings")

# Add the project root directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import django
django.setup()

from UserApp.models import MBCGroup
from CalendarApp.models import Machine

def populate_database(excel_file_path):
    # Read the Excel file into a pandas DataFrame
    df = pd.read_excel(excel_file_path)
    df=df.astype(object)
    df.fillna('', inplace=True) #fill first with a float64 compatible datatype 
        
    # Iterate over rows
    for index, row in df.iterrows():
        try:
            # Try to get the existing record or create a new one
            group, created = MBCGroup.objects.get_or_create(
                group_name = row['Name'],
                location = row['Affiliation'],
            )

            machine_names_string = row['Machine']
            
            if machine_names_string != "" :
                machine_names_list = re.findall(r"\"(.*?)\"", machine_names_string)
                # Query for machines based on the list of names
                machines_queryset = Machine.objects.filter(machine_name__in=machine_names_list)            
                # Assign the machines queryset to the machines field of the Group instance
                group.machines_bought.set(machines_queryset)

            if not created:
                # Update the existing record if it already exists
                group.group_name = row['Name']
                group.location = row['Affiliation']
                group.save()
        except IntegrityError as e:
            print(f"Error processing row {index + 1}: {e}")
    

if __name__ == "__main__":
    # Assuming the script is in the root directory of your project
    excel_file_path = "groups.xlsx"
    populate_database(excel_file_path)


