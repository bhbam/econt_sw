from utils.asic_signals import ASICSignals
for chip in range(100):
    print(f"Starting for chip_{chip}")
    resets = ASICSignals()
    resets.send_reset(reset='hard',i2c='ASIC')
    resets.send_reset(reset='hard',i2c='emulator')
    print(f"Hard reset completed   <<<<<<<<<<<<<<<<<<<<")
