import unittest2 as unittest

import pisi

ADDRESS = 0x10

class MockClock(object):
  @staticmethod
  def sleep(time_sec):
    pass

class MockGPIO(object):
  IN = 1
  OUT = 0
  RISING = 1
  FALLING = 0
  PUD_OFF = 0   # source/c_gpio.h
  PUD_DOWN = 1
  PUD_UP = 2
  BOARD = 10    # source/common.h
  BCM = 11
  HIGH = 1      # source/c_gpio.h
  LOW = 0
  def setup(self, channel, direction, pull_up_down=None, initial=None):
    pass
  def output(self, channel, value):
    pass
  def setmode(self, mode):
    pass

class MockI2C(object):
  def __init__(self, address):
    self.address = address
    self.reg = [0] * 32
    # Reg 00
    self.reg[0] = 0x12
    self.reg[1] = 0x42
    # Reg 01
    self.reg[2] = 0x12
    self.reg[3] = 0x53

  def write_i2c_block_data(self, addr, reg, vals):
    assert addr == self.address
    i = 4   # Start writing at reg2.
    self._Write(i, reg)
    for v in vals:
      i += 1
      self._Write(i, v)

  def read_i2c_block_data(self, addr, reg, length=32):
    assert addr == self.address
    assert length == 32, "Read of wrong length."
    # Return a copy.
    return list(self.reg)

  def _Write(self, addr, value):
    assert addr >= 2 * 2
    assert addr <= 2 * 8
    assert value >= 0
    assert value <= 0xFF
    self.reg[addr] = value


class MockSMBus(object):
  def __init__(self, i2c_num, i2c):
    self._i2c_num = i2c_num
    self._i2c = i2c
  def SMBus(self, num):
    assert num == self._i2c_num
    return self._i2c

class PiSiTest(unittest.TestCase):
  def setUp(self):
    self._i2c = MockI2C(ADDRESS)
    self._smbus = MockSMBus(1, self._i2c)
    self.pisi = pisi.PiSi(MockGPIO(), self._smbus, region=pisi.PiSi.EUROPE, clock=MockClock())

  def testInit(self):
    self.assertEquals(self._i2c.reg[0:16], [
        0x12, 0x42, 0x12, 0x53, 0x40, 0x01, 0x00, 0x00,
        0x08, 0x00, 0x00, 0x10, 0x00, 0x00, 0x81, 0x00,
        ])
    self.assertEquals(self._i2c.reg[16:], [0] * 16)

  def testVolume(self):
    self.assertEquals(self._i2c.reg[11], 0x10)
    oldreg = list(self._i2c.reg)

    self.pisi.SetVolume(7)
    self.assertEquals(self._i2c.reg[11], 0x17)
    self.assertEquals(oldreg[0:11], self._i2c.reg[0:11])
    self.assertEquals(oldreg[12:], self._i2c.reg[12:])

    self.pisi.SetVolume(9)
    self.assertEquals(self._i2c.reg[11], 0x19)
    self.assertEquals(oldreg[0:11], self._i2c.reg[0:11])
    self.assertEquals(oldreg[12:], self._i2c.reg[12:])

    self.pisi.SetVolume(0)
    self.assertEquals(oldreg, self._i2c.reg)

  def testTune(self):
    oldreg = list(self._i2c.reg)

    self.pisi.Tune(100.7)
    self.assertEquals(self._i2c.reg[6], 0x00)
    self.assertEquals(self._i2c.reg[7], 132)
    self.assertEquals(oldreg[0:6], self._i2c.reg[0:6])
    self.assertEquals(oldreg[8:], self._i2c.reg[8:])

    self.pisi.Tune(87.5)
    self.assertEquals(self._i2c.reg[6], 0x00)
    self.assertEquals(self._i2c.reg[7], 0)
    self.assertEquals(oldreg[0:6], self._i2c.reg[0:6])
    self.assertEquals(oldreg[8:], self._i2c.reg[8:])

    self.pisi.Tune(108.0)
    self.assertEquals(self._i2c.reg[6], 0x00)
    self.assertEquals(self._i2c.reg[7], 205)
    self.assertEquals(oldreg[0:6], self._i2c.reg[0:6])
    self.assertEquals(oldreg[8:], self._i2c.reg[8:])

    with self.assertRaises(AssertionError) as context:
      self.pisi.Tune(87.3)
    self.assertIn('Channel out or range', str(context.exception))
