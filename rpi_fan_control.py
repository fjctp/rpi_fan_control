#!/usr/bin/env python3

import os
import signal
import syslog
import RPi.GPIO as GPIO
from math import floor
from time import sleep

# constant
MIN_TEMPERATURE = 70 # below that, turn off the fan
MAX_TEMPERATURE = 85 # above that, fan at 100%

MIN_DUTY_CYCLE = 40
MAX_DUTY_CYCLE = 100

def log_info(msg):
  print(msg)
  syslog.syslog(syslog.LOG_INFO, msg)

def get_temp():
  temp_str = os.popen('/opt/vc/bin/vcgencmd measure_temp').readline()
  try:
    return float(temp_str.replace("temp=","").replace("'C\n",""))
  except ValueError:
    return float(0)

def mapping(value, value_min, value_max, value_new_min, value_new_max):
  safe_value = min(max(value, value_min), value_max)
  alpha = (safe_value-value_min)/(value_max-value_min)
  return alpha*(value_new_max-value_new_min)+value_new_min

class PwmFanControl:
  def __init__(self, pwmPin, period):
    self.pwmPin = pwmPin
    self.period = period
    self.__duty_cycle__ = 0
    
    GPIO.setmode(GPIO.BOARD) # Broadcom pin-numbering scheme
    
    GPIO.setup(self.pwmPin, GPIO.OUT) # PWM pin set as output
    self.pwmHandler = GPIO.PWM(self.pwmPin, 100) # PWM frequency
    self.pwmHandler.start(0)
    
  def __enter__(self):
    return self
    
  def __exit__(self, exc_type, exc_value, traceback):
    self.cleanup()
    
  def start(self):
    try:
      while(True):
        self.__loop__()
    except KeyboardInterrupt:
      pass
    
  def __loop__(self):
    temp = get_temp()
    dc = self.__compute_duty_cycle__(temp)
    
    if self.__duty_cycle__ != dc:
      self.pwmHandler.ChangeDutyCycle(dc)
      log_info('Temp: %2.1f Duty Cycle: %d%%'%(temp, dc))
      self.__duty_cycle__ = dc
      
    sleep(self.period)
    
  def __compute_duty_cycle__(self, temperature):
    if temperature < MIN_TEMPERATURE:
      return 0
    else:
      dc = mapping(temperature,
                   MIN_TEMPERATURE, MAX_TEMPERATURE,
                   MIN_DUTY_CYCLE, MAX_DUTY_CYCLE)
      return int(round(dc, 0))
  
  def cleanup(self):
    log_info('Clean up...')
    self.pwmHandler.stop()
    GPIO.cleanup()
    log_info('Shutdown...')
  

def sig_handler(signum, frame):
  #print('Caught a signal %d'%signum)
  raise KeyboardInterrupt # raise exception to trigger exception handler in class

if __name__=='__main__':
  # TODO move to commandline arguement
  # config variables
  PWM_PIN = 12 
  PERIOD = 20
  
  log_info('Fan control started')
  signal.signal(signal.SIGTERM, sig_handler)
  with PwmFanControl(PWM_PIN, PERIOD) as fc:
    fc.start()
    