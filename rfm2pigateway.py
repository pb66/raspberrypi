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
- share settings file with emoncms
- allow any number of servers (instead of hardcoding 1 local and 1 remote) ?
"""

import serial
import MySQLdb, MySQLdb.cursors
import urllib2, httplib
import time
import logging, logging.handlers
import re
import signal
import os

"""class ServerDataBuffer

Stores server parameters and buffers the data between two HTTP requests

"""
class ServerDataBuffer():

    def __init__(self, gateway, domain, path, apikey, period):
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

    def update_settings(self, domain=None, path=None, apikey=None, period=None):
        """Update server settings."""
        if domain:
            self._domain = domain
        if path:
            self._path = path
        if apikey:
            self._apikey = apikey
        if period:
            self._period = period

    def add_data(self, data):
        """Append timestamped dataset to buffer.

        data (list): node and values (eg: '[node,val1,val2,...]')

        """
        self._gateway.log.debug("Server " + self._domain + self._path + " -> add data: " + str(data))
        # Insert timestamp before data
        dataset = list(data) # Make a distinct copy: we don't want to modify data
        dataset.insert(0,time.time())
        # Append new data set [timestamp, node, val1, val2, val3,...] to _data_buffer
        self._data_buffer.append(dataset)

    def send_data(self):
        """Send data to server."""
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
                self._gateway.log.info("ok")
            else:
                self._gateway.log.info("fail")
        
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
        with open('PID', 'w') as f:
            f.write(str(os.getpid()))

        # Set signal handler to catch SIGINT and shutdown gracefully
        self._exit = False
        signal.signal(signal.SIGINT, self._sigint_handler)
        
        # Initialize logging
        self.log = logging.getLogger('MyLog')
        logfile = logging.handlers.RotatingFileHandler('./rfm2pigateway.log', 'a', 50 * 1024, 1)
        logfile.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
        self.log.addHandler(logfile)
        self.log.setLevel(logging.DEBUG)
        
        # Fetch settings from DB
        self._settings = self._get_DB_settings()
        # If DB connexion fails, exit
        if self._settings is None:
            self.log.error("Connexion to DB failed. Exiting...")
            raise Exception('Connexion to DB failed.')
        self._status_update_timestamp = 0
        
        # Open serial port
        self._ser = self._open_serial_port()
        #print self._ser
        if self._ser is None:
            self.log.error("COM port opening failed. Exiting...")
            raise Exception('COM port opening failed.')
        
        # Initialize serial RX buffer
        self._serial_rx_buf = ''
        
        # Initialize target emoncms server buffers
        self._local_server_buf = ServerDataBuffer(self,
            'localhost',
            '/emoncms', 
            self._settings['apikey'], 
            0)
        
        self._remote_server_buf = ServerDataBuffer(self,
            self._settings['remotedomain'], 
            self._settings['remotepath'],
            self._settings['remoteapikey'],
            30)
        
        self._server_buffers = [self._local_server_buf, self._remote_server_buf]
        
        # Initialize RFM2Pi
        # (force_RFM2Pi_update will force RFM2Pi parameters to be sent)
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
                # Update status in DB to inform emoncms the script is running
                self._raspberrypi_running()
                # Update settings
                self._update_settings()
                # "Thanks for the status update. You've made it crystal clear."
                self._status_update_timestamp = now
            
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
                
                # If emonTX headers (>), discard ?
                if (received[0] == '>'):
                    # WTF ?
                    continue
                
                # Else, frame should be of the form [node val1_lsb val1_msb val2_lsb val2_msb ...]
                elif ((not (len(received) & 1)) or (len(received) < 3)): 
                    # If number of values is not odd or less than 3, frame can't be processed
                    self.log.warning("Misformed RX frame: " + str(received))
                else:
                    # Get node ID
                    node = int(received[0])
                    
                    # Recombine transmitted chars into signed int
                    values = []
                    for i in range(1,len(received),2):
                        value = int(received[i])+256*int(received[i+1])
                        if value > 32768:
                            value = -65536 + value
                        values.append(value)
                    
                    self.log.debug("Node: " + str(node))
                    self.log.debug("Values: " + str(values))
        
                    # Add data to send buffers
                    values.insert(0,node)
                    for server_buf in self._server_buffers:
                        server_buf.add_data(values)
            
            # Send data if time has come
            for server_buf in self._server_buffers:
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
            os.remove('PID')
        except OSError:
            pass
        
        self.log.info("Exiting...")

    def _sigint_handler(self, signal, frame):
        """Catch SIGINT (Ctrl+C)."""
        
        self.log.debug("SIGINT received.")
        # gateway should exit at the end of current iteration.
        self._exit = True

    def _DB_query(self, SQLQuery):
        """Connect to the database and execute a query
        
        SQLQuery (string): SQL query to execute

        Returns the result in the form of a cursor of type dictionnary

        """
        
        db = None
        try:
            db = MySQLdb.connect(host="localhost",user="emoncms",passwd="password",db="emoncms",cursorclass=MySQLdb.cursors.DictCursor)
            cur = db.cursor()
            cur.execute(SQLQuery)
            db.commit()
        except MySQLdb.Error as e:
            self.log.error("Error %d: %s" % (e.args[0],e.args[1]))
            return
        db.close()
        return cur
    
    def _get_DB_settings(self):
        """Fetch settings in the database
        
        Returns a dictionnary

        """
        cur = self._DB_query("SELECT * FROM raspberrypi")
        if cur:
            return cur.fetchone()

    def _set_RFM2Pi_setting(self, setting, value):
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
        """Check settings in DB and update if needed.
        
        force_RFM2Pi_update (boolean): if True, all settings are sent, 
        whether or not they were modified.

        """
        
        # Get settings from DB
        s_new = self._DB_query("SELECT * FROM raspberrypi").fetchone()
        
        # If s_new is None, DB connection failed
        if s_new is None:
            self.log.warning("Database error. Cannot update settings.")
            return
        
        # RFM2Pi settings
        for param in ['baseid', 'frequency', 'sgroup']:
            if ((s_new[param] != self._settings[param]) or force_RFM2Pi_update):
                self._set_RFM2Pi_setting(param,str(s_new[param]))
            
        # Server settings
        self._local_server_buf.update_settings(apikey=self._settings['apikey'])
        
        self._remote_server_buf.update_settings(domain=self._settings['remotedomain'],
                                                path=self._settings['remotepath'],
                                                apikey=self._settings['remoteapikey'])
        
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
                "Couldn't send to server, Exception: " 
                + traceback.format_exc())
        else:
            return ser


    def _raspberrypi_running(self):
        """Update "script running" status in DB."""

        return self._DB_query("UPDATE raspberrypi SET running = '%s'" % str(int(time.time())))


if __name__ == "__main__":

    try:
        gateway = RFM2PiGateway()
    except Exception as e:
        print(e)
    else:    
        gateway.run()
        gateway.close()

