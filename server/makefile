SHELL := /bin/bash
.SHELLFLAGS := -e

run-server: create-db create-virtualenv
	source env/bin/activate \
	./manage.py runserver

install-mysql:
	@echo "Installing MySQL"
	sudo apt update \
	&& sudo apt install default-mysql-server

mysql_secure_installation:
	sudo mysql_secure_installation

create-db: install-mysql create_db.sql
	@echo "Creating database"
	sudo mysql -u root < create_db.sql

create-virtualenv:
	python3 -m venv env \
	&& source env/bin/activate \
	&& pip install -r requirements.txt

#To remove all migration history and create a single migration file representing the current state without dropping the database, follow these steps:
reset-migrations:
	#Delete Migration Files: Remove all migration files in each app's migrations directory, except for the __init__.py file.
	rm -rf UserApp/migrations/*py
	rm -rf CalendarApp/migrations/*py
	touch UserApp/migrations/__init__.py
	touch CalendarApp/migrations/__init__.py
	./manage.py makemigrations UserApp
	./manage.py makemigrations CalendarApp
