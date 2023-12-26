# -*- coding: utf-8 -*-

import os

def rename_settings_files(folder_path):
    # Define the file paths
    emilio_settings_path = os.path.join(folder_path, 'settings_emilio.py')
    marco_settings_path = os.path.join(folder_path, 'settings_marco.py')
    default_settings_path = os.path.join(folder_path, 'settings.py')

    # Check if emilio_settings_path exists
    if os.path.exists(emilio_settings_path):
        # Rename files
        os.rename(default_settings_path, marco_settings_path)
        os.rename(emilio_settings_path, default_settings_path)
        print("Files renamed successfully.")
    else:
        if os.path.exists(marco_settings_path):
            # Rename files
            os.rename(default_settings_path, emilio_settings_path)
            os.rename(marco_settings_path, default_settings_path)
            print("Files renamed successfully.")
        else:
            print("File not found:", emilio_settings_path)

if __name__ == "__main__":
    # Replace with your actual folder path
    folder_path = r"C:\Users\emili\OneDrive - Università degli Studi di Torino\Documenti\Lab\docs\Centro MBC\Booking App Python\BookingMBC\server\BookingMBC"

    rename_settings_files(folder_path)
