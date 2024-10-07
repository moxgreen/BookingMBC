CREATE DATABASE bookingmbc;

CREATE USER 'bookingmbc'@'%' IDENTIFIED BY 'bookimgmbc';

GRANT ALL PRIVILEGES ON bookingmbc.* TO 'bookingmbc'@'%';
GRANT ALL PRIVILEGES ON bookingmbc.* TO 'bookingmbc'@'localhost';

FLUSH PRIVILEGES;