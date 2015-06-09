import RPi.GPIO as GPIO 
import smbus 

import pisi

p = pisi.PiSi(GPIO, smbus, pisi.PiSi.EUROPE)
p.SetVolume(5)
p.Tune(87.6)
