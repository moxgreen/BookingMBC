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

from UserApp.models import UserProfile
from CalendarApp.models import Machine  # Adjust the import path based on your project structure

def populate_database(excel_file_path):
    # Read the Excel file into a pandas DataFrame
    df = pd.read_excel(excel_file_path)
    df=df.astype(object)
    df.fillna('', inplace=True) #fill first with a float64 compatible datatype 
    
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b'
    
    # Iterate over columns using iteritems
    for mn in df.columns:
        print(f"Machine: {mn}")
        
        # Iterate over rows for each column
        for s in df[mn]:
            # Use re.search to find the first email address in the input string
            match = re.search(email_pattern, s)
            
            # If a match is found, return the extracted email address; otherwise, return None
            ema = match.group() if match else ""
            if ema == "": continue
            print(f"  User email: {ema}")
            try:
                usp=UserProfile.objects.get(user__email=ema)
            except UserProfile.DoesNotExist:
                print(f"  email: {ema} not registered")
                continue
            m=Machine.objects.get(machine_name=mn)
            usp.machines4ThisUser.add(m)
            try:
                usp.save()
            except IntegrityError as e:
                print(f"Error {e} processing email: {ema}")

            

if __name__ == "__main__":
    # Assuming the script is in the root directory of your project
    excel_file_path = "assign_exclusive.xlsx"
    populate_database(excel_file_path)


