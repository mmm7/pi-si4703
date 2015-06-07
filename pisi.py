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

  def Tune(self, freq_mhz):
    # If BAND 05h[7:6] = 00, then
    #   Freq (MHz) = Spacing (MHz) x Channel + 87.5 MHz.
    # If BAND 05h[7:6] = 01, BAND 05h[7:6] = 10, then
    #   Freq (MHz) = Spacing (MHz) x Channel + 76 MHz.
    freq_khz = int(freq_mhz * 1000)
    channel = (freq_khz - self._bandstart) / self._spacing
    assert channel >= 0, (
        "Channel out or range. [%f, %d, %d]" %
        (freq_mhz, self._bandstart, self._spacing))
    assert channel < 512, (
        "Channel out or range. [%f, %d, %d]" %
        (freq_mhz, self._bandstart, self._spacing))
    # Set TUNE.
    self._SetRegister(3, 0x8000 + channel)
    self._WriteRegisters()
    self._clock.sleep(1)
    # Unset TUNE.
    self._SetRegister(3, 0x0000 + channel)
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
      self._spacing = 200
      self._bandstart = 87500
      self._SetRegister(4, 0x0000)
      self._SetRegister(5, 0x0000)
    elif self._region == PiSi.EUROPE:
      self._spacing = 100
      self._bandstart = 87500
      self._SetRegister(4, 0x0800)
      self._SetRegister(5, 0x0010)
    elif self._region == PiSi.AUSTRALIA:
      self._spacing = 200
      self._bandstart = 87500
      self._SetRegister(4, 0x0800)
      self._SetRegister(5, 0x0000)
    elif self._region == PiSi.JAPAN:
      self._spacing = 100
      self._bandstart = 76000
      self._SetRegister(4, 0x0800)
      self._SetRegister(5, 0x0090)
    elif self._region == PiSi.JAPAN_WIDE:
      self._spacing = 100
      self._bandstart = 76000
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
