import socket
import os, time, datetime
IP = "192.168.1.48"
# IP = "127.0.0.1"
PORT = 9999
SIZE = 10240
FORMAT = "utf-8"
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
print("socket created")
server.bind((IP,PORT))
server.listen()
print("server started...")
print("Waiting fom request from client")

while 1:

    conn, addr = server.accept()


    msg = conn.recv(SIZE).decode()
    message, chip_,pll_width_th, thresold_max_width_,thresold_second_max_width_, max_IO_delay_scan_width_thresold_, second_max_IO_delay_scan_width_thresold_ = msg.split('|')
    chip = int(chip_)


    print(f"Received request from client: {message} for chip_{chip}")
    if message == 'start':



        voltage, current, over_all_test, rw_test, pll_test, phase_width_test, io_scan_test, pll_width, eRx_0,eRx_1,eRx_2,eRx_3,eRx_4,eRx_5,eRx_6,eRx_7,eRx_8,eRx_9,eRx_10,eRx_11,eRx2_0,eRx2_1,eRx2_2,eRx2_3,eRx2_4,eRx2_5,eRx2_6,eRx2_7,eRx2_8,eRx2_9,eRx2_10,eRx2_11,eTx_0,eTx_1,eTx_2,eTx_3,eTx_4,eTx_5,eTx_6,eTx_7,eTx_8,eTx_9,eTx_10,eTx_11,eTx_12,eTx2_0,eTx2_1,eTx2_2,eTx2_3,eTx2_4,eTx2_5,eTx2_6,eTx2_7,eTx2_8,eTx2_9,eTx2_10,eTx2_11,eTx2_12, test_end_check = 1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1
        conn.send(bytes(f"{voltage}|{current}|{over_all_test}|{rw_test}|{pll_test}|{phase_width_test}|{io_scan_test}|{pll_width}|{eRx_0}|{eRx_1}|{eRx_2}|{eRx_3}|{eRx_4}|{eRx_5}|{eRx_6}|{eRx_7}|{eRx_8}|{eRx_9}|{eRx_10}|{eRx_11}|{eRx2_0}|{eRx2_1}|{eRx2_2}|{eRx2_3}|{eRx2_4}|{eRx2_5}|{eRx2_6}|{eRx2_7}|{eRx2_8}|{eRx2_9}|{eRx2_10}|{eRx2_11}|{eTx_0}|{eTx_1}|{eTx_2}|{eTx_3}|{eTx_4}|{eTx_5}|{eTx_6}|{eTx_7}|{eTx_8}|{eTx_9}|{eTx_10}|{eTx_11}|{eTx_12}|{eTx2_0}|{eTx2_1}|{eTx2_2}|{eTx2_3}|{eTx2_4}|{eTx2_5}|{eTx2_6}|{eTx2_7}|{eTx2_8}|{eTx2_9}|{eTx2_10}|{eTx2_11}|{eTx2_12}|{test_end_check}",f"{FORMAT}"))
        conn.close()
