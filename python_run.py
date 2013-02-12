# TODO : 
# - update RFM2Pi status
# - time stuff

import serial, MySQLdb, MySQLdb.cursors, urllib2

"""
Log function
"""
def log (text):
# Placeholder for log function
    print text

"""
getDBSettings
Fetch settings in the database
    # DB keys :
    # userid, apikey, sgroup ,frequency, baseid, remotedomain, remotepath, remoteapikey, remotesend
Returns a dictionnary
"""
def getDBSettings():
    db = None
    try:
        db=MySQLdb.connect(host="localhost",user="emoncms",passwd="password",db="emoncms",cursorclass=MySQLdb.cursors.DictCursor)
        cur = db.cursor()
        cur.execute("SELECT * FROM raspberrypi")
        settings = cur.fetchone()
    
    except MySQLdb.Error, e:
        log("Error %d: %s" % (e.args[0],e.args[1]))
        return None
    finally:    
        if db:    
            db.close()

    return settings

"""
Heres is the real stuff
"""
# Initialization

# Open serial port
ser = serial.Serial('/dev/ttyAMA0', 9600)

# Initialize data string
data = '['

# Until death comes
while True:
    
    # Read serial RX
    received = ser.readline()
    # Dev / debug : Simulate SERIAL RX if not using serial link for real
    #received = ' 10 14 7'
    
    log("Serial RX : "+received)
    
    # Get an array out of the space separated string
    received = received.strip().split(' ')
    
    # If emonTX headers (>), discard ?
    if (received[0] == '>'):
        # WTF ?
        continue
    
    # Else, treat value
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
        
        log("Node : "+node)
        log("Values : "+str(values))
    
        # Write data string
        time = 0
        data+='['+str(time)+','+str(node)
        for val in values:
            data+=','+str(val)
        data+=']'
    
        #log("data : "+data)
    

    # Check settings from times to times
    # What for ? group, freq, baseid ?
    
    # Send data once in a while
    if True: # Need to add a time condition here, but before that, introduce 'timestamps'
    
        # Close last bracket in data string
        data+=']'
        log("data : "+data)
    
        # Get server settings in DB
        settings = getDBSettings()
    
        # Assemble local URL string
        url_string_localhost = "http://localhost/emoncms/input/bulk.json?apikey="+settings['apikey']+"&data="+data
        log(url_string_localhost)
    
        # Assemble remote URL string
        url_string_remote = "http://"+settings['remotedomain']+settings['remotepath']+"/input/bulk.json?apikey="+settings['remoteapikey']+"&data="+data
        log(url_string_remote)
    
        # Re-initialize data string
        data = '['
    
        # Send
        log("Sending to localhost...")
        result = urllib2.urlopen(url_string_localhost)
        if (result.readline() == 'ok'):
            log("ok")
        else:
            log("fail")
        log("Sending to remote server...")
        result = urllib2.urlopen(url_string_remote)
        if (result.readline() == 'ok'):
            log("ok")
        else:
            log("fail")
    

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
 
