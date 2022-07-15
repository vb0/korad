#!/usr/bin/python
import serial
import time
import threading
import sys
import termios
import tty
import re

lock=threading.Lock()

fd = sys.stdin.fileno()
old_settings = termios.tcgetattr(fd)

amp_format=re.compile("^[0-9]\.[0-9][0-9][0-9]")
vol_format=re.compile("^[0-9][0-9]\.[0-9][0-9]")

ser=serial.Serial('/dev/ttyACM0', timeout=10)
ser.flushInput()

safe_delay=0.1

def to_ascii(str0):
	return bytes(str0, 'ascii')

def turn_on():
	ser.write(to_ascii('OUT1'))
	time.sleep(safe_delay)

def turn_off():
	ser.write(to_ascii('OUT0'))
	time.sleep(0.1)

def get_idn():
	time.sleep(0.1)
	ser.flushInput()
	ser.write(to_ascii('*IDN?'))
	return ser.read(16).decode('ascii')

def get_stored_current():
	time.sleep(0.1)
	ser.flushInput()
	ser.write(to_ascii('ISET1?'))
	tmp1=ser.read(5).decode('ascii')
	ser.read(1)
	if re.match(amp_format,tmp1):
		return(int(tmp1[:1] + tmp1[2:]))
	else:
		sys.stderr.write('Error in get_stored_current read\n')
		return(0)

def get_stored_voltage():
	time.sleep(safe_delay)
	ser.flushInput()
	ser.write(to_ascii('VSET1?'))
	tmp1=ser.read(5).decode('ascii')
	if re.match(vol_format,tmp1):
		return(int(tmp1[:2] + tmp1[3:] + "0"))
	else:
		sys.stderr.write('Error in get_stored_voltage read\n')
		return(0)

def get_output_voltage():
	time.sleep(safe_delay)
	ser.flushInput()
	ser.write(to_ascii('VOUT1?'))
	tmp1=ser.read(5).decode('ascii')
	if re.match(vol_format,tmp1):
		return(int(tmp1[:2] + tmp1[3:] + "0"))
	else:
		sys.stderr.write('Error in get_output_voltage read\n')
		return(0)

def get_output_current():
	time.sleep(safe_delay)
	ser.flushInput()
	ser.write(to_ascii('IOUT1?'))
	tmp1=ser.read(5).decode('ascii')
	if re.match(amp_format,tmp1):
		return(int(tmp1[:1] + tmp1[2:]))
	else:
		sys.stderr.write('Error in get_output_current read\n')
		return(0)

def set_current(current):
	if current>5095: current=5095
	if current<0: current=0
	time.sleep(safe_delay)
	ser.flushInput()
	to_write='ISET1:'+str(int(current/1000))+'.'+"{:0>3d}".format(int(current-1000*int(current/1000)))
	ser.write(to_ascii(to_write))

def set_voltage(voltage):
	if voltage>30000: voltage=30000
	if voltage<0: voltage=0
	time.sleep(safe_delay)
	ser.flushInput()
	to_write='VSET1:'+"{:0>2d}".format(int(voltage/1000))+'.'+"{:0>2d}".format(int(int(voltage-1000*int(voltage/1000))/10))
	ser.write(to_ascii(to_write))

char=""

s_current=get_stored_current()
s_voltage=get_stored_voltage()

def keypress():
	global lock
	global char
	global s_current
	global s_voltage
	while True:
		tty.setraw(fd)
		tmp_char = sys.stdin.read(1)
		termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
		lock.acquire()
		char = tmp_char
		if tmp_char=='i': s_current=s_current-1
		if tmp_char=='I': s_current=s_current+1
		if tmp_char=='v': s_voltage=s_voltage-10
		if tmp_char=='V': s_voltage=s_voltage+10
		if tmp_char=='q':
			lock.release()
			exit(0)
		lock.release()

threading.Thread(target=keypress).start()

t0=time.time()
v=get_output_voltage()
t=time.time()
i=get_output_current()
mwh=0
mah=0

while True:
	v_old=v
	i_old=i
	t_old=t
	v=get_output_voltage()
	t=time.time()
	i=get_output_current()
	v_stored=get_stored_voltage()
	i_stored=get_stored_voltage()
	if s_current != i_stored: set_current(s_current)
	if s_voltage != v_stored: set_voltage(s_voltage)
	w=i*v/1000000.
	mah=mah+(t-t_old)*(i+i_old)/2/3600.
	mwh=mwh+(t-t_old)*(i+i_old)*(v+v_old)/4/3600/1000.
	print(str(i)+"mA",str("{0:.2f}".format(v/1000.))+"V",str("{0:.5f}".format(w))+"W",'%s' % float('%.5g' % mwh) +"mWh",'%s' % float('%.5g' % mah)+"mAh",str("{0:.1f}".format(t-t0))+"s","SET:"+str(get_stored_current())+"mA",str("{0:.2f}".format(get_stored_voltage()/1000.))+"V\r")
	lock.acquire()
	char_cpy = char
	if char_cpy != "":
		if char_cpy=='O': turn_on()
		if char_cpy=='o': turn_off()
		if char_cpy=='q':
			lock.release();
			exit(0)
		if char_cpy=='a': print("Vad un 'a' (I see an 'a')\r")
		char=""
	lock.release()
	time.sleep(0.4)
