# Primitive backup utility
## Schedule daily or weekly backup
* crontab -e
* 0 {hour} * * * {path}/run_backup.sh

## Restore backup
* mysql --host=127.0.0.1 --port=30002 -u root -p
* use bookingmbc
* source {backup}