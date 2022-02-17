import os
import uhal
from .uhal_config import names

import logging
logging.basicConfig()
logger = logging.getLogger('utils:fc')
logger.setLevel(logging.INFO)

class FastCommands:
    """Class to handle sending fast command signals over uhal"""

    def __init__(self):
        """Initialization class to setup connection manager and device"""
        self.man = uhal.ConnectionManager("file://connection.xml")
        self.dev = self.man.getDevice("mylittlememory")

    def configure_fc(self,read=False):
        """
        Configure FC
        Do not enable L1A (since this disables link resets)
        """
        if read:
            fc_stream = self.dev.getNode(names['fc']+".command.enable_fast_ctrl_stream").read()
            orb_sync = self.dev.getNode(names['fc']+".command.enable_orbit_sync").read()
            glob_l1a = self.dev.getNode(names['fc']+".command.global_l1a_enable").read()
            self.dev.dispatch()
            logger.info('fc stream %i orb_sync %i glob_l1a %i '%(fc_stream,orb_sync,glob_l1a))
        else:
            self.dev.getNode(names['fc']+".command.enable_fast_ctrl_stream").write(0x1);
            self.dev.getNode(names['fc']+".command.enable_orbit_sync").write(0x1);
            self.dev.getNode(names['fc']+".command.global_l1a_enable").write(0);
            self.dev.dispatch()
    
    def enable_l1a(self,read=False):
        if read:
            r =  self.dev.getNode(names['fc']+".command.global_l1a_enable").read()
            self.dev.dispatch()
            logger.info('glob_l1a %i '%r)
        else:
            self.dev.getNode(names['fc']+".command.global_l1a_enable").write(1);
            self.dev.dispatch()

    def chipsync(self):
        self.dev.getNode(names['fc']+".request.chipsync").write(1);
        self.dev.dispatch()

    def read_command_delay(self):
        d = self.dev.getNode(names['fc']+".command_delay").read();
        self.dev.dispatch()
        logger.info('command_delay %i'%int(d))

    def set_command_delay(self):
        dev.getNode(names['fc']+".command_delay").write(1);
        dev.dispatch()

    def send_l1a(self):
        """
        Send L1A once
        """
        self.dev.getNode(names['fc']+".command.global_l1a_enable").write(0x1);
        self.dev.getNode(names['fc']+".periodic0.enable").write(0x0); # to get a L1A once
        #self.dev.getNode(names['fc']+".periodic0.enable").write(0x1); # to get a L1A every orbit
        self.dev.getNode(names['fc']+".periodic0.flavor").write(0); # 0 to get a L1A 
        self.dev.getNode(names['fc']+".periodic0.enable_follow").write(0); # does not depend on other generator
        self.dev.getNode(names['fc']+".periodic0.bx").write(3500);
        self.dev.getNode(names['fc']+".periodic0.request").write(0x1);
        self.dev.dispatch()
    
        import time
        time.sleep(0.001)
        l1a_counter = self.dev.getNode(names['fc-recv']+".counters.l1a").read()
        self.dev.dispatch()
        logger.debug('L1A counter %i'%(int(l1a_counter)))
