import gc
import esp
import machine

print('LPG Monitoring System')

esp.osdebug(None)
machine.freq(80000000)
gc.collect()