import time

class PiSi(object):
  USA = 0
  EUROPE = 1
  AUSTRALIA = 2
  JAPAN = 3
  JAPAN_WIDE = 4

  def __init__(self, gpio, smbus, region, i2c_num=1, address=0x10, control_gpio=17, clock=time):
    self._i2c = smbus.SMBus(i2c_num)
    self._address = address
    self._clock = clock
    self._region = region
    self._InitGPIO(gpio, control_gpio, clock)
    self._reg = [0] * 32
    self._Initialize()
    self._SetUpRegion()

  def SetVolume(self, vol):
    self._reg[11] = (self._reg[11] & 0xF0) | (vol & 0x0F)
    self._WriteRegisters()

  @staticmethod
  def _InitGPIO(GPIO, control_gpio, clock):
    GPIO.setmode(GPIO.BCM) #board numbering
    GPIO.setup(control_gpio, GPIO.OUT) 
    GPIO.setup(0, GPIO.OUT)  #SDA or SDIO 
     
    #put SI4703 into 2 wire mode (I2C) 
    GPIO.output(0,GPIO.LOW) 
    clock.sleep(.1) 
    GPIO.output(control_gpio, GPIO.LOW) 
    clock.sleep(.1) 
    GPIO.output(control_gpio, GPIO.HIGH) 
    clock.sleep(.1) 

  def _Initialize(self):
    # Initialize oscillator.
    self._SetRegister(7, 0x8100)
    self._WriteRegisters()
    self._clock.sleep(1)

    #write x4001 to reg 2 to turn off mute and activate IC
    self._SetRegister(2, 0x4001)
    self._WriteRegisters()

  def _SetUpRegion(self):
    if self._region == PiSi.USA:
      self._SetRegister(4, 0x0000)
      self._SetRegister(5, 0x0000)
    elif self._region == PiSi.EUROPE:
      self._SetRegister(4, 0x0800)
      self._SetRegister(5, 0x0010)
    elif self._region == PiSi.AUSTRALIA:
      self._SetRegister(4, 0x0800)
      self._SetRegister(5, 0x0000)
    elif self._region == PiSi.JAPAN:
      self._SetRegister(4, 0x0800)
      self._SetRegister(5, 0x0090)
    elif self._region == PiSi.JAPAN_WIDE:
      self._SetRegister(4, 0x0800)
      self._SetRegister(5, 0x0050)
    self._WriteRegisters()
    
  def _SetRegister(self, reg, value):
    assert reg >=2, "Register %d out of ragne for writing."
    assert reg <=7, "Register %d out of range for writing."
    self._reg[reg*2 + 0] = (value >> 8) & 0xFF
    self._reg[reg*2 + 1] = (value     ) & 0xFF

  def _WriteRegisters(self):
    self._i2c.write_i2c_block_data(self._address, self._reg[4], self._reg[5:16])
    self._clock.sleep(.1) 
