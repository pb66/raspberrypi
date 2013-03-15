#!/usr/bin/env python

"""

  All Emoncms code is released under the GNU Affero General Public License.
  See COPYRIGHT.txt and LICENSE.txt.

  ---------------------------------------------------------------------
  Emoncms - open source energy visualisation
  Part of the OpenEnergyMonitor project:
  http://openenergymonitor.org

"""

"""
TODO : 
- add new parameters instead of hardcoding (log level, sending interval...)
- allow https
- allow any number of servers (instead of hardcoding 1 local and 1 remote) ?
"""

import serial
import MySQLdb, MySQLdb.cursors
import urllib2, httplib
import time, datetime
import logging, logging.handlers
import re
import signal
import os
import csv

"""class ServerDataBuffer

Stores server parameters and buffers the data between two HTTP requests

"""
class ServerDataBuffer():

    def __init__(self, gateway, domain, path, apikey, period, active):
        """Create a server data buffer initialized with server settings.
        
        domain (string): domain name (eg: 'domain.tld')
        path (string): emoncms path with leading slash (eg: '/emoncms')
        apikey (string): API key with write access
        period (int): sending interval in seconds
        
        """
        self._gateway = gateway
        self._domain = domain
        self._path = path
        self._apikey = apikey
        self._period = period
        self._data_buffer = []
        self._last_send = time.time()
        self._active = active

    def update_settings(self, domain=None, path=None, apikey=None, period=None, active=None):
        """Update server settings."""
        if domain is not None:
            self._domain = domain
        if path is not None:
            self._path = path
        if apikey is not None:
            self._apikey = apikey
        if period is not None:
            self._period = period
        if active is not None:
            self._active = active

    def add_data(self, data):
        """Append timestamped dataset to buffer.

        data (list): node and values (eg: '[node,val1,val2,...]')

        """
       
        if not self._active:
            return
        
        self._gateway.log.debug("Server " + self._domain + self._path + " -> add data: " + str(data))
        
        # Insert timestamp before data
        dataset = list(data) # Make a distinct copy: we don't want to modify data
        dataset.insert(0,time.time())
        # Append new data set [timestamp, node, val1, val2, val3,...] to _data_buffer
        self._data_buffer.append(dataset)

    def send_data(self):
        """Send data to server."""
        
        if not self._active:
            return

        # Prepare data string with the values in data buffer
        now = time.time()
        data_string = '['
        for data in self._data_buffer:
            data_string += '['
            data_string += str(int(round(data[0]-now)))
            for sample in data[1:]:
                data_string += ','
                data_string += str(sample)
            data_string += '],'
        data_string = data_string[0:-1]+']' # Remove trailing comma and close bracket 
        self._data_buffer = []
        self._gateway.log.debug("Data string: " + data_string)
        
        # Prepare URL string of the form
        # 'http://domain.tld/emoncms/input/bulk.json?apikey=12345&data=[[-10,10,1806],[-5,10,1806],[0,10,1806]]'
        url_string = "http://"+self._domain+self._path+"/input/bulk.json?apikey="+self._apikey+"&data="+data_string
        self._gateway.log.debug("URL string: " + url_string)

        # Send data to server
        # TODO : manage failures: currently, data is just lost
        # We could keep it and retry, and trash after given amount of time/data
        self._gateway.log.info("Sending to " + self._domain + self._path)
        try:
            result = urllib2.urlopen(url_string)
        except urllib2.HTTPError as e:
            self._gateway.log.warning("Couldn't send to server, HTTPError: " + str(e.code))
        except urllib2.URLError as e:
            self._gateway.log.warning("Couldn't send to server, URLError: " + str(e.reason))
        except httplib.HTTPException:
            self._gateway.log.warning("Couldn't send to server, HTTPException")
        except Exception:
            import traceback
            self._gateway.log.warning("Couldn't send to server, Exception: " + traceback.format_exc())
        else:
            if (result.readline() == 'ok'):
                self._gateway.log.info("Send ok")
            else:
                self._gateway.log.warning("Send failure")
        
        # Update _last_send
        self._last_send = time.time()

    def check_time(self):
        """Check if it is time to send data to server.
        
        return True if sending interval has passed since last time

        """
        now = time.time()
        if (now - self._last_send > self._period):
            return True
    
    def has_data(self):
        """Check if buffer has data
        
        Return True if data buffer is not empty.
        
        """
        return (self._data_buffer != [])


"""class RFM2PiGateway

Monitors the serial port for data from RFM2Pi and sends data to local or remote 
emoncms servers through ServerDataBuffer instances.

"""
class RFM2PiGateway():
    
    def __init__(self):
        """Setup an RFM2Pi gateway."""

        # Store PID in a file to allow SIGINTability
        with open(os.path.join(os.path.dirname(__file__), 
                               'rfm2pigateway/PID'),
                  'w') as f:
            f.write(str(os.getpid()))

        # Set signal handler to catch SIGINT and shutdown gracefully
        self._exit = False
        signal.signal(signal.SIGINT, self._sigint_handler)
        
        # Initialize logging
        self.log = logging.getLogger('MyLog')
        logfile = logging.handlers.RotatingFileHandler(
            os.path.join(os.path.dirname(__file__), 
                         'rfm2pigateway/rfm2pigateway.log'),
            'a', 5000 * 1024, 1)
        logfile.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
        self.log.addHandler(logfile)
        self.log.setLevel(logging.DEBUG)
        
        # Fetch settings
        self._settings = self._get_settings()
        
        # If settings can't be obtained, exit
        if self._settings is None:
            self.log.critical("Couldn't get settings.")
            raise Exception("Couldn't get settings.")
        self._status_update_timestamp = 0
        self._time_update_timestamp = 0
        
        # Open serial port
        self._ser = self._open_serial_port()
        if self._ser is None:
            self.log.critical("COM port opening failed. Exiting...")
            raise Exception('COM port opening failed.')
        
        # Initialize serial RX buffer
        self._serial_rx_buf = ''
        
        # Initialize target emoncms server buffer set
        self._server_buffers = {}
        
        # Update settigns (emoncms server buffers and RFM2Pi)
        # (force_RFM2Pi_update forces RFM2Pi parameters to be sent)
        self._update_settings(force_RFM2Pi_update=True)
    
    def run(self):
        """Launch the gateway.
        
        Monitor the COM port and process data.
        Check settings on a regular basis.

        """

        # Until asked to stop
        while not self._exit:
            
            # Update settings and status every second
            now = time.time()
            if (now - self._status_update_timestamp > 1):
                # Update "running" status to inform emoncms the script is running
                self._raspberrypi_running()
                # Update settings
                self._update_settings()
                # "Thanks for the status update. You've made it crystal clear."
                self._status_update_timestamp = now
            
            # Send time every minute to synchronize emonGLCD
            if (now - self._time_update_timestamp > 60):
                self._send_time()
                self._time_update_timestamp = now

            # Read serial RX
            self._serial_rx_buf = self._serial_rx_buf + self._ser.readline()
        
            # If full line was read, process
            if ((self._serial_rx_buf != '') and 
                (self._serial_rx_buf[len(self._serial_rx_buf)-1] == '\n')):
        
                # Remove CR,LF
                self._serial_rx_buf = re.sub('\\r\\n', '', self._serial_rx_buf)
                
                # Log data
                self.log.info("Serial RX: " + self._serial_rx_buf)
                
                # Get an array out of the space separated string
                received = self._serial_rx_buf.strip().split(' ')
                
                # Empty serial_rx_buf
                self._serial_rx_buf = ''
                
                # If information message, discard
                if ((received[0] == '>') or (received[0] == '->')):
                    continue

                # Else,frame should be of the form 
                # [node val1_lsb val1_msb val2_lsb val2_msb ...]
                # with number of elements odd and at least 3
                elif ((not (len(received) & 1)) or (len(received) < 3)):
                    self.log.warning("Misformed RX frame: " + str(received))
                
                # Else, process frame
                else:
                    try:
                        received = [int(val) for val in received]
                    except Exception:
                        self.log.warning("Misformed RX frame: " + str(received))
                    else:
                        # Get node ID
                        node = received[0]
                        
                        # Recombine transmitted chars into signed int
                        values = []
                        for i in range(1,len(received),2):
                            value = received[i] + 256 * received[i+1]
                            if value > 32768:
                                value -= 65536
                            values.append(value)
                        
                        self.log.debug("Node: " + str(node))
                        self.log.debug("Values: " + str(values))
            
                        # Add data to send buffers
                        values.insert(0,node)
                        for server_buf in self._server_buffers.itervalues():
                            server_buf.add_data(values)
            
            # Send data if time has come
            for server_buf in self._server_buffers.itervalues():
                if server_buf.check_time():
                    if server_buf.has_data():
                        server_buf.send_data()
        
            # Sleep until next iteration
            time.sleep(1);
         
    def close(self):
        """Close gateway. Do some cleanup before leaving."""
        
        # Close serial port
        self.log.debug("Closing serial port.")
        self._ser.close()

        # Delete PID file
        try:
            os.remove(os.path.join(os.path.dirname(__file__), 
                                   'rfm2pigateway/PID'))
        except OSError:
            pass
        
        self.log.info("Exiting...")

    def _sigint_handler(self, signal, frame):
        """Catch SIGINT (Ctrl+C)."""
        
        self.log.debug("SIGINT received.")
        # gateway should exit at the end of current iteration.
        self._exit = True

    def _get_settings(self):
        """Get settings
        
        Returns a dictionnary

        """
        try:
            result = urllib2.urlopen("http://localhost/emoncms/raspberrypi/get.json")
            result = result.readline()
            # result is of the form
            # {"userid":"1","sgroup":"210",...,"remoteprotocol":"http:\\/\\/"}
            result = result[1:-1].split(',')
            # result is now of the form
            # ['"userid":"1"',..., '"remoteprotocol":"http:\\/\\/"']
            settings = {}
            # For each setting, separate key and value
            for s in result:
                # We can't just use split(':') as there can be ":" inside a value 
                # (eg: "http://")
                s = csv.reader([s], delimiter=':').next() 
                settings[s[0]] = s[1].replace("\\","")
            return settings

        except Exception:
            import traceback
            self.log.warning("Couldn't get settings, Exception: " + traceback.format_exc())
            return

    def _set_rfm2pi_setting(self, setting, value):
        """Send a configuration parameter to the RFM2Pi through COM port.
        
        setting (string): setting to be sent, can be one of the following:
          baseid, frequency, sgroup
        value (string): value for this setting
        
        """
        
        self.log.info("Setting RFM2Pi | %s: %s" % (setting, value))
        if setting == 'baseid':
            self._ser.write(value+'i')
        elif setting == 'frequency':
            self._ser.write(value+'b')
        elif setting == 'sgroup':
            self._ser.write(value+'g')
        time.sleep(1);
    
    def _update_settings(self, force_RFM2Pi_update=False):
        """Check settings and update if needed.
        
        force_RFM2Pi_update (boolean): if True, all settings are sent, 
        whether or not they were modified.

        """
        
        # Get settings
        s_new = self._get_settings()

        # If s_new is None, no answer to settings request
        if s_new is None:
            return

        # RFM2Pi settings
        for param in ['baseid', 'frequency', 'sgroup']:
            if ((s_new[param] != self._settings[param]) or force_RFM2Pi_update):
                self._set_rfm2pi_setting(param,str(s_new[param]))

        # Server settings
        if 'local' not in self._server_buffers:
            self._server_buffers['local'] = ServerDataBuffer(
                    gateway = self,
                    domain = 'localhost',
                    path = '/emoncms', 
                    apikey = s_new['apikey'], 
                    period = 0, 
                    active = True)
        else:
            self._server_buffers['local'].update_settings(
                    apikey = s_new['apikey'])
        
        if 'remote' not in self._server_buffers:
            self._server_buffers['remote'] = ServerDataBuffer(
                    gateway = self,
                    domain = s_new['remotedomain'], 
                    path = s_new['remotepath'],
                    apikey = s_new['remoteapikey'],
                    period = 30,
                    active = int(s_new['remotesend']))
        else: 
            self._server_buffers['remote'].update_settings(
                    domain = s_new['remotedomain'],
                    path = s_new['remotepath'],
                    apikey = s_new['remoteapikey'],
                    active = int(s_new['remotesend']))
        
        self._settings = s_new
    
    def _open_serial_port(self):
        """Open serial port."""

        self.log.debug("Opening serial port: /dev/ttyAMA0")
        
        try:
            ser = serial.Serial('/dev/ttyAMA0', 9600, timeout = 0)
        except serial.SerialException as e:
            self.log.error(e)
        except Exception:
            import traceback
            self.log.error(
                "Couldn't open serial port, Exception: " 
                + traceback.format_exc())
        else:
            return ser

    def _raspberrypi_running(self):
        """Update "script running" status."""
        
        try:
            result = urllib2.urlopen("http://localhost/emoncms/raspberrypi/setrunning.json")
        except Exception:
            import traceback
            self.log.warning("Couldn't update \"running\" status, Exception: " + traceback.format_exc())
           
    def _send_time(self):
        """Send time over radio link to synchronize emonGLCD."""

        now = datetime.datetime.now()

        self.log.debug("Sending time for emonGLCD: %d:%d" % (now.hour, now.minute))

        self._ser.write("%02d,00,%02d,00,s" % (now.hour, now.minute))


if __name__ == "__main__":

    try:
        gateway = RFM2PiGateway()
    except Exception as e:
        print(e)
    else:    
        gateway.run()
        gateway.close()

