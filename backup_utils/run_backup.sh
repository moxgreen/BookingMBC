#!/bin/bash

echo "Running daily backup"
mkdir booking_mbc_backup__
mysqldump --host=127.0.0.1 --port=30002 -u root -pbookimgmbc bookingmbc > $(pwd)/booking_mbc_backup__/dump.sql
tar -zcvf $(pwd)/booking_mbc_$(date +%y_%m_%d)_backup.tar.gz $(pwd)/booking_mbc_backup__
openssl aes-256-cbc -a -salt -pbkdf2 -pass pass:$C_PASSWORD_MBC -in $(pwd)/booking_mbc_$(date +%y_%m_%d)_backup.tar.gz -out $(pwd)/booking_mbc_backup/booking_mbc_$(date +%y_%m_%d)_backup.tar.gz.enc
rm -rf $(pwd)/booking_mbc_$(date +%y_%m_%d)_backup.tar.gz
rm -rf $(pwd)/booking_mbc_backup__
cd booking_mbc_backup && git add . && git commit -m "daily_backup" && git push https://Marco-Masera:$github_token@github.com/Marco-Masera/booking_mbc_backup.git

#Remove old backups to avoid saturating the disk with old backups
directory="booking_mbc_backup"

# Maximum number of backups to keep
M=28

# Check if the directory exists
if [ ! -d "$directory" ]; then
    echo "Directory not found: $directory"
    exit 1
fi

# Count the number of files in the directory
num_files=$(ls -1 "$directory" | wc -l)

# If the number of files is greater than M, delete the oldest files
if [ "$num_files" -gt "$M" ]; then
    # Get the list of files sorted by modification time (oldest first)
    files_to_delete=$(ls -1t "$directory" | tail -n $(($num_files - $M)))
    
    # Iterate over the files to delete and remove them
    for file in $files_to_delete; do
        rm "$directory/$file"
        echo "Deleted: $file"
    done
else
    echo "Number of files ($num_files) is not greater than $M. No files deleted."
fi