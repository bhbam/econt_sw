
import os
import subprocess
IP = "192.168.1.48"
CLIENT_FOLDER = "data"
chip = 999
# folder_name = f"chip_{chip}"
# folder_path = os.path.join(CLIENT_FOLDER, folder_name)
# if not os.path.exists(folder_path):
    # os.makedirs(folder_path)

# Set the remote server's IP address, username, and password
remote_host = IP
remote_username = 'HGCAL_dev'
remote_password = 'daq5HGCAL!'

# Set the path of the directory you want to copy on the remote server
remote_dir = f'/home/HGCAL_dev/bbbam/econt_sw/econt_sw/data/chip_{chip}'

# Set the path of the local directory where you want to copy the files
local_dir = 'data'

# Build the `rsync` command as a list of arguments
rsync_command = ['rsync', '-avz', f'{remote_username}@{remote_host}:{remote_dir}', local_dir]

# Run the `rsync` command with the `subprocess.run()` function
result = subprocess.run(rsync_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, input=f"{remote_password}\n", encoding='ascii')

# Print the output and errors, if any
print(result.stdout)
print(result.stderr)
