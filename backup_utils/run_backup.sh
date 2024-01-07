#!/bin/bash


echo "Running daily backup"
mkdir booking_mbc_backup
mysqldump --host=127.0.0.1 --port=30001 -u root -ptriplex triplex > $(pwd)/booking_mbc_backup/myDBDump
tar -zcvf $(pwd)/booking_mbc_$(date +%y_%m_%d)_backup.tar.gz $(pwd)/booking_mbc_backup
rm -rf $(pwd)/booking_mbc_backup/
