#!/usr/bin/python
import serial
import time
ser = serial.Serial('/dev/ttyACM0', timeout=10)
ser.flushInput()

safe_delay=0.1

def turn_on():
	ser.write('OUT1')
	time.sleep(safe_delay)

def turn_off():
        ser.write('OUT0')
        time.sleep(0.1)

def get_idn():
	time.sleep(0.1)
	ser.flushInput()
	ser.write('*IDN?')
	return ser.read(16)

def get_stored_current():
	time.sleep(0.1)
        ser.flushInput()
        ser.write('ISET1?')
        return ser.read(5)
	ser.read(1)

def get_stored_voltage():
	time.sleep(safe_delay)
        ser.flushInput()
        ser.write('VSET1?')
        return ser.read(5)

def get_output_voltage():
        time.sleep(safe_delay)
        ser.flushInput()
        ser.write('VOUT1?')
        return float(ser.read(5))

def get_output_current():
        time.sleep(safe_delay)
        ser.flushInput()
        ser.write('IOUT1?')
        return float(ser.read(5))

t0=time.time()
v=get_output_voltage()
t=time.time()
i=get_output_current()
wh=0

while True:
	v_old=v
	i_old=i
	t_old=t
	v=get_output_voltage()
	t=time.time()
	i=get_output_current()
	w=i*v
	wh=wh+(t-t_old)*(i+i_old)*(v+v_old)/4/3600	
	print i,v,w,wh,t-t0,get_stored_voltage(),get_stored_current() 

