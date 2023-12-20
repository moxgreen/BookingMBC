CREATE USER 'bookingmbc'@'localhost' IDENTIFIED BY 'bookingmbc';
GRANT ALL PRIVILEGES ON *.* TO 'bookingmbc'@'localhost' WITH GRANT OPTION;
CREATE DATABASE IF NOT EXISTS bookingmbc;
