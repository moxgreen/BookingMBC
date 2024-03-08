#!/bin/bash

echo "Running daily backup"
mkdir booking_mbc_backup__
mysqldump --host=127.0.0.1 --port=30002 -u root -pbookimgmbc bookingmbc > $(pwd)/booking_mbc_backup__/dump.sql
tar -zcvf $(pwd)/booking_mbc_$(date +%y_%m_%d)_backup.tar.gz $(pwd)/booking_mbc_backup__
openssl aes-256-cbc -a -salt -pbkdf2 -pass pass:$C_PASSWORD_MBC -in $(pwd)/booking_mbc_$(date +%y_%m_%d)_backup.tar.gz -out $(pwd)/booking_mbc_backup/booking_mbc_$(date +%y_%m_%d)_backup.tar.gz.enc
rm -rf $(pwd)/booking_mbc_$(date +%y_%m_%d)_backup.tar.gz
rm -rf $(pwd)/booking_mbc_backup__
cd booking_mbc_backup && git add . && git commit -m "daily_backup" && git push https://Marco-Masera:$github_token@github.com/Marco-Masera/booking_mbc_backup.git