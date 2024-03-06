# Primitive backup utility
## Schedule daily or weekly backup
* crontab -e
* 0 {hour} * * * {path}/run_backup.sh

## Restore backup
* Remove encryption openssl aes-256-cbc -d -a -pbkdf2 -in booking_mbc_24_03_06_backup.tar.gz.enc -out out
* de-zip to retrieve dump tar -xvf out
* mysql --host=127.0.0.1 --port=30002 -u root -p
* use bookingmbc
* source {backup}

