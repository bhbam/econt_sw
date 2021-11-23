import argparse
import os
import zmq_controller as zmqctrl

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Align links')
    parser.add_argument('--start-server', dest="start_server", action='store_true', default=False, help='start servers directly in script (for debugging is better to do it separately)')
    args = parser.parse_args()

    server={'ASIC': '5554', 'emulator': '5555'}
    addr={'ASIC':0, 'emulator':1}

    env = os.environ.copy()
    from subprocess import PIPE, Popen
    cmds = {}
    cwds = {}
    for key in server.keys():
        cmds[key] = ['python3', '-u', 'zmq_server.py', '--addr', '%i'%(0x20+addr[key]), '--server', server[key]]
        cwds[key] = './zmq_i2c'

    # i2c for alignment
    orbsyn_cnt_snapshot = {# 'ASIC': 7,
                           'ASIC': 3,
                           'emulator': 3, # 1
                    }
    orbsyn_cnt_load_val = {'ASIC': 0,
                           'emulator': 0
                       }
    match_pattern_val = 0x9cccccccaccccccc

    procs = {}
    if args.start_server:
        for key in server.keys():
            procs[key] = Popen(cmds[key], cwd=cwds[key],stdout=PIPE, universal_newlines=True, env=env)

    i2c_sockets = {}
    for key in server.keys():
        i2c_sockets[key] = zmqctrl.i2cController("localhost", str(server[key]), "configs/align.yaml")
        i2c_sockets[key].yamlConfig['ECON-T']['RW']['ALIGNER_ALL']['registers']['orbsyn_cnt_load_val']['value'] = orbsyn_cnt_load_val[key]
        i2c_sockets[key].yamlConfig['ECON-T']['RW']['ALIGNER_ALL']['registers']['orbsyn_cnt_snapshot']['value'] = orbsyn_cnt_snapshot[key]
        i2c_sockets[key].yamlConfig['ECON-T']['RW']['ALIGNER_ALL']['registers']['match_pattern_val']['value'] = match_pattern_val
        i2c_sockets[key].configure()

        # read back i2c 
        read_socket = i2c_sockets[key].read_config("configs/align.yaml")
        print('TX sync word %s '%key,hex(read_socket['RW']['FMTBUF_ALL']['tx_sync_word']))

    # phase alignment for IO
    os.system('python testing/uhal-align_on_tester.py --step tester-phase')
    os.system('python testing/uhal-align_on_tester.py --step asic-word')

    # read i2c registers (select and status)
    read_emulator = i2c_sockets['emulator'].read_config("configs/align.yaml","read")
    read_asic = i2c_sockets['ASIC'].read_config("configs/align.yaml","read")

    orbsyn_cnt_snapshot_asic = read_asic['RW']['ALIGNER_ALL']['orbsyn_cnt_snapshot']
    orbsyn_cnt_snapshot_emu = read_emulator['RW']['ALIGNER_ALL']['orbsyn_cnt_snapshot']
    print('Orbit cnt snapshot emulator %i, ASIC %i'%(orbsyn_cnt_snapshot_emu,orbsyn_cnt_snapshot_asic))

    for i in range(12):
        # status should be 0x3
        # alignment patern should be in snapshot
        print('LINK %i:'%i)
        snapshot = read_asic['RO']['CH_ALIGNER_%iINPUT_ALL'%i]['snapshot']
        sel = read_asic['RO']['CH_ALIGNER_%iINPUT_ALL'%i]['select']
        status = read_asic['RO']['CH_ALIGNER_%iINPUT_ALL'%i]['status']
        orbsyn_cnt_snapshot = read_asic['RW']['ALIGNER_ALL']['orbsyn_cnt_snapshot']
        print('Status: ',hex(status), ' Snapshot: ',hex(snapshot),' Select value: ',hex(sel))
        print('Snapshot ',hex(snapshot >> sel))
        try:
            assert status==0x03
        except AssertionError:
            print('Failed to align ECON-T channel %i, status: %i'%(i,status))
            raise

    # relative alignment for IO
    os.system('python testing/uhal-align_on_tester.py --step asic-tester')
    
    # terminate i2c servers
    for key,proc in procs.items():
        proc.terminate()

