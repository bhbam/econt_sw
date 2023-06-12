

import socket
import os, time, datetime
# from tqdm import tqdm
import sqlite3
from sqlite3_database import create_database, add_many_column, show_all_plan
import os
import paramiko
import warnings
from cryptography.utils import CryptographyDeprecationWarning
# for chip in range(100):
test_end_check = -1
# chip = 999999
IP = "192.168.1.48"
# IP = "127.0.0.1"
PORT = 9999
# SIZE = 1024
SIZE = 1024
FORMAT = "utf-8"
CLIENT_FOLDER = "data"
for chip in range(100):
    # chip = 9999
    test_start_time = time.time()
    folder_name = f"chip_{chip}"
    pll_width_th, max_with_thresold, second_max_width_thresold, max_IO_delay_scan_width_thresold, second_max_IO_delay_scan_width_thresold =11, 3, 2, 13, 12
    #  Socket to talk to server
    print("Connecting to  server…")
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((IP, PORT))

    try:
        print(f"Sending request to server …")
        client.send(bytes(f"start|{chip}|{pll_width_th}|{max_with_thresold}|{second_max_width_thresold}|{max_IO_delay_scan_width_thresold}|{second_max_IO_delay_scan_width_thresold}",FORMAT))

        print(f"start request  sent to server")
    except:
        print(f"Error in sending message to server for chip_{chip}!!!!!")
    # time.sleep(150)
    now = datetime.datetime.now()
    datetime_now = now.strftime("%Y-%m-%d_%H:%M:%S")
    try:
        #  Get the reply from server
        message2 = client.recv(SIZE).decode()
        data = message2.split('|')


        chip_n = chip
        date_time = datetime_now
        voltage = data[0]
        current = data[1]
        overall_test = data[2]
        rw_test = data[3]
        pll_test = data[4]
        phase_width_test_eRx = data[5]
        input_word_alignment_test = data[6]
        phase_width_test_eTx = data[7]
        output_alignment_test = data[8]
        alignment_bypass_test = data[9]
        comparing_various_config_test = data[10]
        track_mode_test = data[11]
        pll_th = pll_width_th
        max_eRx_th = max_with_thresold
        sec_max_eRx_th = second_max_width_thresold
        max_eTx_th = max_IO_delay_scan_width_thresold
        sec_max_eTx_th = second_max_IO_delay_scan_width_thresold
        pll_width = int(data[12])
        eRx_0 = int(data[13])
        eRx_1 = int(data[14])
        eRx_2 = int(data[15])
        eRx_3 = int(data[16])
        eRx_4 = int(data[17])
        eRx_5 = int(data[18])
        eRx_6 = int(data[19])
        eRx_7 = int(data[20])
        eRx_8 = int(data[21])
        eRx_9 = int(data[22])
        eRx_10 = int(data[23])
        eRx_11 = int(data[24])
        eRx2_0 = int(data[25])
        eRx2_1 = int(data[26])
        eRx2_2 = int(data[27])
        eRx2_3 = int(data[28])
        eRx2_4 = int(data[29])
        eRx2_5 = int(data[30])
        eRx2_6 = int(data[31])
        eRx2_7 = int(data[32])
        eRx2_8 = int(data[33])
        eRx2_9 = int(data[34])
        eRx2_10 = int(data[35])
        eRx2_11 = int(data[36])
        eTx_0 = int(data[37])
        eTx_1 = int(data[38])
        eTx_2 = int(data[39])
        eTx_3 = int(data[40])
        eTx_4 = int(data[42])
        eTx_5 = int(data[42])
        eTx_6 = int(data[43])
        eTx_7 = int(data[44])
        eTx_8 = int(data[45])
        eTx_9 = int(data[46])
        eTx_10 = int(data[47])
        eTx_11 = int(data[48])
        eTx_12 = int(data[49])
        eTx2_0 = int(data[50])
        eTx2_1 = int(data[51])
        eTx2_2 = int(data[52])
        eTx2_3 = int(data[53])
        eTx2_4 = int(data[54])
        eTx2_5 = int(data[55])
        eTx2_6 = int(data[56])
        eTx2_7 = int(data[57])
        eTx2_8 = int(data[58])
        eTx2_9 = int(data[59])
        eTx2_10 = int(data[60])
        eTx2_11 = int(data[61])
        eTx2_12 = int(data[62])
        test_end_check = data[63]
        print("Received data for database")

        if os.path.exists("Econt_database.db") == False:
            create_database()
        stuff=[(chip_n, date_time, voltage, current, overall_test, rw_test, pll_test, phase_width_test_eRx, input_word_alignment_test, phase_width_test_eTx, output_alignment_test, alignment_bypass_test, comparing_various_config_test, track_mode_test, pll_th, max_eRx_th, sec_max_eRx_th,max_eTx_th,sec_max_eTx_th, pll_width, eRx_0,eRx_1,eRx_2,eRx_3,eRx_4,eRx_5,eRx_6,eRx_7,eRx_8,eRx_9,eRx_10,eRx_11,eRx2_0,eRx2_1,eRx2_2,eRx2_3,eRx2_4,eRx2_5,eRx2_6,eRx2_7,eRx2_8,eRx2_9,eRx2_10,eRx2_11,eTx_0,eTx_1,eTx_2,eTx_3,eTx_4,eTx_5,eTx_6,eTx_7,eTx_8,eTx_9,eTx_10,eTx_11,eTx_12,eTx2_0,eTx2_1,eTx2_2,eTx2_3,eTx2_4,eTx2_5,eTx2_6,eTx2_7,eTx2_8,eTx2_9,eTx2_10,eTx2_11,eTx2_12)]
        add_many_column(stuff)
        # add_many_column([data])
        show_all_plan()
        test_end_time = time.time()
        print("Test time :", test_end_time - test_start_time)
    except:
        if test_end_check == 1:
            print("Test ended but can not updated to database!!!")
        else:
            test_end_check = 0
            print("Error with test on server !!!!!!")
    print("Test completed ---->", test_end_check)
# print(""" Copying files from server """)
# #
# # """ Creating the folder """
#
# folder_path = os.path.join(CLIENT_FOLDER, folder_name)
# if not os.path.exists(folder_path):
#     os.makedirs(folder_path)
# #
#
#
#
# files = [ f"best_phase_scan_seting_chip_{chip}.txt",
# f"error_counts_chip_{chip}.csv",
# f"from_io_delayscanchip_{chip}.csv",
# f"good_capSelected_values_chip_{chip}.txt",
# f"io_delay_width_comparion_chip_{chip}.txt",
# f"logFile_chip_{chip}.log",
# f"phase_width_comparion_chip_{chip}.txt",
# f"pll_capSelect_scanchip_{chip}.csv",
# f"power_voltage_current_chip_{chip}.txt",
# f"prbs_counters_scan_0.05schip_{chip}.csv",
# f"rw_pair_one_comparion_chip_{chip}.txt",
# f"rw_pair_zero_comparion_chip_{chip}.txt",
# f"trackmode1_phaseSelectchip_{chip}.csv",
# f"trackmode2_phaseSelectchip_{chip}.csv",
# f"trackmode3_phaseSelectchip_{chip}.csv",
# f"width_of_io_scan_seting_chip_{chip}.txt",
# f"width_of_phase_scan_seting_chip_{chip}.txt"]
#
# warnings.filterwarnings("ignore", category=CryptographyDeprecationWarning)
# ssh = paramiko.SSHClient()
# ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
# ssh.connect(hostname= IP, username='HGCAL_dev', password='daq5HGCAL!', port=22)
# sftp_client = ssh.open_sftp()
# for file_name in files:
#     try:
#         sftp_client.get(f'/home/HGCAL_dev/bbbam/econt_sw/econt_sw/data/{file_name}',f'{folder_path}/{file_name}')
#     except FileNotFoundError:
#         print("NO SUCH FILE", file_name)
#         os.system(f'rm  {folder_path}/{file_name}')
# sftp_client.close()
# ssh.close()
#
#
#
#
#
# total_end_time = time.time()
# test_time_taken = test_end_time - start_time
# total_time_taken = total_end_time - start_time
#
# print("test time taken----->  ", test_time_taken)
# print("Total time taken------>  ", total_time_taken)
# # time.sleep(1)
