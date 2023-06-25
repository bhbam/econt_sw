from set_econt import startup,set_phase,set_phase_of_enable,set_runbit,read_status,set_fpga,word_align,output_align,bypass_align,bypass_compare
from utils.asic_signals import ASICSignals
from i2c import I2C_Client
from PRBS import scan_prbs
import numpy as np
import time
import datetime
i2cClient=I2C_Client(forceLocal=1)


# #-----------------------------------------

# # Initialize
startup()
set_fpga()
track_mode_test = -1
track_mode_1_test = -1
track_mode_2_test = -1
track_mode_3_test = -1


err_counts, best_setting = scan_prbs(32,'ASIC',0.05,range(0,12),1,verbose=0,odir='data',tag='')
print("PRBS Error Counts----",err_counts)

# print("error counts for setting 0", err_counts[0:4])
error_counts = [[  0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0],
 [  0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0],
 [255, 255,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0],
 [255, 255,   0,   3 ,  0,   0,   0,   0, 103,   0,   0,   0],
 [255, 255, 255, 255, 255,  24, 255,   0, 255,  37, 255,   0],
 [255,   2, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255],
 [  0,   0, 255, 255, 255, 255, 255, 255,   0, 255, 255, 255],
 [  0,   0,   0,   0,   0, 255,   0, 255,   0,  77,   4, 255],
 [  0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0],
 [  0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0],
 [255, 255,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0],
 [255, 255,   0,   0,   0,   0,   0,   0,  17,   0,   0,   0],
 [255, 255, 255, 255, 255,  61, 255,   0, 255,  77, 255,   0],
 [255,  12, 255, 255, 255, 255, 255, 255, 255, 255, 255, 174],
 [  0,   0, 255, 255, 255, 255,  32, 255,   0, 255, 255, 255]]

best_setting =  [7, 7, 9, 9, 9, 2, 9, 2, 8, 9, 9, 2]

test_start_time = time.time()
for trackmode in range(1, 4):
    i2cClient.call(args_name='EPRXGRP_TOP_trackMode', args_value=f'{trackmode}')
    phaseSelect_vals = []
    error_t =[]
    if trackmode == 3:
        set_phase(best_setting=','.join([str(i) for i in best_setting]))
    for trainchannel in range(0, 5):

        i2cClient.call(args_name='CH_EPRXGRP_*_trainChannel', args_value='1')
        i2cClient.call(args_name='CH_EPRXGRP_*_trainChannel', args_value='0')
        x = i2cClient.call(args_name='CH_EPRXGRP_*_status_phaseSelect',args_i2c='ASIC')
        selected_phase_settings = [x['ASIC']['RO'][f'CH_EPRXGRP_{channel}INPUT_ALL']['status_phaseSelect'] for channel in range(0, 12)]
        phaseSelect_vals.append(selected_phase_settings)
        print(f"-----selected_phase_settings for trackmode {trackmode} for run {trainchannel}--------------", selected_phase_settings)
        errors_ =[]
        for i,j in enumerate(selected_phase_settings):
          errors_.append(np.transpose(err_counts)[i][j])
          total_errors1 = np.sum(errors_)
        error_t.append(total_errors1)
    total_error2 = np.sum(error_t)
    if trackmode == 1:
        if total_error2 == 0:
            track_mode_1_test = 1
            print(f"trackmode {trackmode} test passed <<<  ")
        else:
            track_mode_1_test = 0
            print(f"trackmode {trackmode} test failed !!!  ")
            print(f"total error in trackmode {trackmode} in all run ---  ", total_error2)
    if trackmode == 2:
        if total_error2 == 0:
            track_mode_2_test = 1
            print(f"trackmode {trackmode} test passed <<<   ")
        else:
            track_mode_2_test = 0
            print(f"trackmode {trackmode} test failed !!!  ")
            print(f"total error in trackmode {trackmode} in all run ---  ", total_error2)
    if trackmode == 3:
        if total_error2 == 0:
            track_mode_3_test = 1
            print(f"trackmode {trackmode} test passed <<<   ")
        else:
            track_mode_3_test = 0
            print(f"trackmode {trackmode} test failed !!!  ")
            print(f"total error in trackmode {trackmode} in all run ---  ", total_error2)
if track_mode_1_test==1 and track_mode_2_test==1 and track_mode_3_test==1:
    track_mode_test = 1
    print(f"trackmode test passed <<<")
else:
    track_mode_test = 0
    print(f"trackmode test failed !!!")
test_end_time = time.time()
print("total time taken ", test_end_time - test_start_time)
