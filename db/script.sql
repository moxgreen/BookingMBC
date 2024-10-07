CREATE DATABASE IF NOT EXISTS bookingmbc;
CREATE USER 'bookingmbc'@'localhost' IDENTIFIED BY 'bookingmbc';
GRANT ALL PRIVILEGES ON bookingmbc.* TO 'bookingmbc'@'localhost' WITH GRANT OPTION;
FLUSH PRIVILEGES;