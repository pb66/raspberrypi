# TODO : 
# - check settings on a regular basis
# - allow any number of servers
# - add new parameters instead of hardcoding (log level, sending interval...)
# - register PID to allow SIGINT from GUI
# - cleanup, reorganize functions / classes, follow coding rules 
#       http://www.python.org/dev/peps/pep-0008/
import serial
import MySQLdb, MySQLdb.cursors
import urllib2, httplib
import time
import logging, logging.handlers
import re
import signal

"""class ServerDataBuffer

Stores server parameters and buffers the data between two HTTP requests

"""
class serverdatabuffer():

    def __init__(self, domain, path, apikey, period):
        """Create a server data buffer initialized with server settings.
        
        domain (string): domain name (eg: 'domain.tld')
        path (string): emoncms path with leading slash (eg: '/emoncms')
        apikey (string): API key with write access
        period (int): sending interval in seconds
        
        """
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
        log.debug('Server ' + self._domain + self._path + ' -> add data: ' + str(data))
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
        log.debug('Data string: ' + data_string)
        
        # Prepare URL string of the form
        # 'http://domain.tld/emoncms/input/bulk.json?apikey=12345&data=[[-10,10,1806],[-5,10,1806],[0,10,1806]]'
        url_string = "http://"+self._domain+self._path+"/input/bulk.json?apikey="+self._apikey+"&data="+data_string
        log.debug('URL string: ' + url_string)

        # Send data to server
        # TODO : manage failures: currently, data is just lost
        # We could keep it and retry, and trash after given amount of time/data
        log.info("Sending to " + self._domain + self._path)
        try:
            result = urllib2.urlopen(url_string)
            if (result.readline() == 'ok'):
                log.info("ok")
            else:
                log.info("fail")
        except urllib2.HTTPError, e:
            log.warning("Couldn't send to server, HTTPError: " + str(e.code))
        except urllib2.URLError, e:
            log.warning("Couldn't send to server, URLError: " + str(e.reason))
        except httplib.HTTPException, e:
            log.warning("Couldn't send to server, HTTPException")
        except Exception:
            import traceback
            log.warning("Couldn't send to server, Exception: " + traceback.format_exc())
        
        # Update _last_send
        self._last_send = time.time()

    def checktime(self):
        """Check if it is time to send data to server.
        
        return True if sending interval has passed since last time

        """
        now = time.time()
        if (now - self._last_send > self._period):
            return True
    
    def has_data(self):
        """Return True if data buffer is not empty."""
        return (self._data_buffer != [])


"""
DBQuery : connect to the database
Returns a cursor of type Dictionnary
"""
def DBQuery(SQLQuery):
    db = None
    try:
        db=MySQLdb.connect(host="localhost",user="emoncms",passwd="password",db="emoncms",cursorclass=MySQLdb.cursors.DictCursor)
        cur = db.cursor()
        cur.execute(SQLQuery)
        db.commit()
    except MySQLdb.Error, e:
        log.error("Error %d: %s" % (e.args[0],e.args[1]))
        return
    db.close()
    return cur

"""
getDBSettings
Fetch settings in the database
Returns a dictionnary
"""
def getDBSettings():
    cur = DBQuery("SELECT * FROM raspberrypi")
    if cur:
        return cur.fetchone()

"""
raspberrypi_running()
Update RFM2Pi link status
"""
def raspberry_running():
    return DBQuery("UPDATE raspberrypi SET running = '%s'" % str(int(time.time())))

"""
setRFM2PiSettings()
Set RFM2Pi settings
"""
def setRFM2PiSettings(ser):
    # TODO : only send if different
    s = getDBSettings()
    if s:
        log.info("Sending RFM2Pi settings")
        log.info("Base id: %d, Frequency: %d, Group: %d" % (s['baseid'], s['frequency'], s['sgroup']))
        ser.write(str(s['baseid'])+'i')
        time.sleep(1); # Does this really work ?
        ser.write(str(s['frequency'])+'b')
        time.sleep(1);
        ser.write(str(s['sgroup'])+'g')
        time.sleep(1);

"""
sigint_handler()
"""
def sigint_handler(signal, frame):
    """Catch SIGINT (Ctrl+C)."""
    global sigint_received
    log.debug("SIGINT received.")
    sigint_received = True

"""
Here is the real stuff
"""
# Set signal handler to catch SIGINT
sigint_received = False
signal.signal(signal.SIGINT, sigint_handler)

# Initialize the logging
log = logging.getLogger('MyLog')
logfile = logging.handlers.RotatingFileHandler('./RFM2Py.log', 'a', 50 * 1024, 1)
logfile.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
log.addHandler(logfile)
log.setLevel(logging.DEBUG)

# Fetch settings
settings = getDBSettings()

# Initialize serial RX buffer
serial_rx_buf = ''

# Initialize target emoncms server buffers
local_server_buf = serverdatabuffer('localhost',
                                    '/emoncms', 
                                    settings['apikey'], 
                                    0)

remote_server_buf = serverdatabuffer(settings['remotedomain'], 
                                     settings['remotepath'],
                                     settings['remoteapikey'],
                                     30)

server_buffers = [local_server_buf, remote_server_buf]

# Open serial port
ser = serial.Serial('/dev/ttyAMA0', 9600, timeout = 0)

# Initialize RFM2Pi
setRFM2PiSettings(ser)

# Until asked to stop
while not sigint_received:
    
    # Read serial RX
    serial_rx_buf = serial_rx_buf + ser.readline()

    # If full line was read, process
    if ((serial_rx_buf != '') and (serial_rx_buf[len(serial_rx_buf)-1] == '\n')):

        # Remove CR,LF
        serial_rx_buf = re.sub('\\r\\n', '', serial_rx_buf)
        
        # Log data
        log.info("Serial RX: " + serial_rx_buf)
        
        # Update RFM2Pi link status
        raspberry_running()
        
        # Get an array out of the space separated string
        received = serial_rx_buf.strip().split(' ')
        
        # Empty serial_rx_buf
        serial_rx_buf = ''
        
        # If emonTX headers (>), discard ?
        if (received[0] == '>'):
            # WTF ?
            continue
        
        # Else, frame should be of the form [node val1_lsb val1_msb val2_lsb val2_msb ...]
        elif ((not (len(received) & 1)) or (len(received) < 3)): 
            # If number of values is not odd or less than 3, frame can't be processed
            log.warning("Misformed RX frame: " + str(received))
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
            
            log.debug("Node: " + str(node))
            log.debug("Values: " + str(values))

            # Add data to send buffers
            values.insert(0,node)
            for server_buf in server_buffers:
                server_buf.add_data(values)
    
    # Send data if time has come
    for server_buf in server_buffers:
        if server_buf.checktime():
            if server_buf.has_data():
                server_buf.send_data()


    # Update settings from times to times
    #RFM2Pi settings
    #if True:
    #    setRFM2PiSettings(ser)
    #server settings

log.info("Exiting...")

