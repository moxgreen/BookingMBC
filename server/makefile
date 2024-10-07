SH=bash

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