# TODO : 
# - time stuff
# - use threads because serial read is blocking
# - function names consistency... http://www.python.org/dev/peps/pep-0008/
import serial
import MySQLdb, MySQLdb.cursors
import urllib2
import time
import logging, logging.handlers
import re



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
Here is the real stuff
"""
# Initialize the logging
log = logging.getLogger('MyLog')
logfile = logging.handlers.RotatingFileHandler('./RFM2Py.log', 'a', 50 * 1024, 1)
logfile.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
log.addHandler(logfile)
log.setLevel(logging.DEBUG)

# Open serial port
ser = serial.Serial('/dev/ttyAMA0', 9600, timeout = 0)

# Initialize RFM2Pi
setRFM2PiSettings(ser)

# Initialize data string
data = '['

serial_rx_buf = ''

# Until death comes
while True:
    
    # Read serial RX
    serial_rx_buf = serial_rx_buf + ser.readline()

    # If full line was read, process
    if ((serial_rx_buf != '') and (serial_rx_buf[len(serial_rx_buf)-1] == '\n')):

        # Remove CR,LF
        serial_rx_buf = re.sub('\\r\\n', '', serial_rx_buf)
        
        # Log data
        log.info("Serial RX : " + serial_rx_buf)
        
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
            node = received[0]
            
            # Recombine transmitted chars into signed int
            values = []
            for i in range(1,len(received),2):
                value = int(received[i])+256*int(received[i+1])
                if value > 32768:
                    value = -65536 + value
                values.append(value)
            
            log.debug("Node : "+node)
            log.debug("Values : "+str(values))
        
            # Write data string
            timestamp = 0
            data+='['+str(timestamp)+','+str(node)
            for val in values:
                data+=','+str(val)
            data+=']'
            #log.debug("data : "+data)
    
        

    # Update RFM2Pi settings from times to times
    #if True:
    #    setRFM2PiSettings(ser)

    # Send data once in a while
    # If there is data : # Need to add time condition...
    if (data != '['):
    
        # Close last bracket in data string
        data+=']'
        log.debug("data : "+data)
    
        # Get server settings in DB
        # TODO : do something if settings = None (couldn't access DB)
        settings = getDBSettings()
        #log.debug(str(settings))
    
        # Assemble local URL string
        url_string_localhost = "http://localhost/emoncms/input/bulk.json?apikey="+settings['apikey']+"&data="+data
        log.debug(url_string_localhost)
    
        # Assemble remote URL string
        url_string_remote = "http://"+settings['remotedomain']+settings['remotepath']+"/input/bulk.json?apikey="+settings['remoteapikey']+"&data="+data
        log.debug(url_string_remote)
    
        # Re-initialize data string
        data = '['

        # Send
        log.info("Sending to localhost...")
        try:
            result = urllib2.urlopen(url_string_localhost)
            if (result.readline() == 'ok'):
                log.info("ok")
            else:
                log.info("fail")
        except urllib2.HTTPError, e:
            log.warning("Couldn't send to localhost, HTTPError: " + str(e.code))
        except urllib2.URLError, e:
            log.warning("Couldn't send to localhost, URLError: " + str(e.reason))
        except httplib.HTTPException, e:
            log.warning("Couldn't send to localhost, HTTPException")
        except Exception:
            import traceback
            log.warning("Couldn't send to localhost, Exception: " + traceback.format_exc())
        
        log.info("Sending to remote server...")
        try:
            result = urllib2.urlopen(url_string_remote)
            if (result.readline() == 'ok'):
                log.info("ok")
            else:
                log.info("fail")
        except urllib2.HTTPError, e:
            log.warning("Couldn't send to remote server, HTTPError: " + str(e.code))
        except urllib2.URLError, e:
            log.warning("Couldn't send to remote server, URLError: " + str(e.reason))
        except httplib.HTTPException, e:
            log.warning("Couldn't send to remote server, HTTPException")
        except Exception:
            import traceback
            log.warning("Couldn't send to remote server, Exception: " + traceback.format_exc())
        

    # Notes

    #http://docs.python.org/2/howto/urllib2.html
    
    #result = urllib2.urlopen("http://"+settings['remotedomain']+settings['remotepath']+"/time/local.json?apikey="+settings['remoteapikey'])
    #if ("t" == result.read(1)):
    #    print "cool"
    #else:
    #    print "not cool"
    
    """ Format
    Sending remote data
    GET /emoncms/input/bulk.json?apikey=12345&data=[[0,10,1806],[0,10,1806],[4,10,1806],[7,10,1806],[11,10,1806],[15,10,1800],[19,10,1800],[23,10,1800],[26,10,1806],[30,10,1806],[34,10,1800]] HTTP/1.1
    """

