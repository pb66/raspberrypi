#Raspberry PI emoncms module

This module is to be used with an emoncms installed on the PI to interface with an RFM12 to PI board in a seemless fashion.

Full documentation for setting up a raspberry pi installation of emoncms can be found here:

[Build from scratch](http://emoncms.org/site/docs/raspberrypibuild)

Or you can skip all the build steps and download a pre-built image:

[Using ready-to-go image](http://emoncms.org/site/docs/raspberrypiimage)

##Features
- set the emoncms account to send data to
- set the RFM12 frequency
- set the RFM12 group
- set the RFM12 board node id.
- gateway scripts to forward data from serial port to local and remote emonCMS

##Installation

Install one of the two available gateway scripts to let them run on startup

### PHP Gateway

Install serial PHP libraries

    $ sudo apt-get install php-pear php5-dev
    $ sudo pecl install channel://pecl.php.net/dio-0.0.6
    $ sudo nano /etc/php5/cli/php.ini

add extension=dio.so to file in the beginning of the ;Dynamic Extensions; section on line 843 

[Ctrl+X] then [y] then [Enter] to save and exit

Install rfm12piphp gateway service:

    sudo cp /var/www/emoncms/Modules/raspberrypi/rfm12piphp /etc/init.d/
    sudo chmod 755 /etc/init.d/rfm12piphp
    sudo update-rc.d rfm12piphp defaults

**2 MAY 2013 UPDATED rfm12piphp** recall the above 3 commands to update your rfm12piphp script after fetching the latest changes from github, then restart the rfm12piphp service.

Start the service with:

    $ sudo /etc/init.d/rfm12piphp start
    
the following commands can also be used to control the service

    $ sudo service rfm12piphp status
    $ sudo service rfm12piphp start
    $ sudo service rfm12piphp stop
    $ sudo service rfm12piphp restart

#### Debugging

It is often useful to log the output of the rfm12piphp service to check that its working ok. Logging is turned off as default to reduce the amount of writes to the SD card. To turn logging on just add the word log to the end of the service command, ie:

    sudo service rfm12piphp restart log

To view the log:
    
    $ tail -F -n 40  /var/log/rfm12piphp.log

To prolong the life of your SD Card turn off logging when its not needed by calling restart without the log:

    sudo service rfm12piphp restart

### RFM2Pi Gateway (python script)

  Install python serial port and mySQL modules

    $ sudo aptitude install python-serial python-mysqldb
  
  Ensure the script is executable
    $ chmod 755 /var/www/emoncms/Modules/raspberrypi/rfm2pigateway.py
  
  Create groupe emoncms and make user pi part of it

    $ sudo groupadd emoncms
    $ sudo usermod -a -G emoncms pi

  Create a directory for the logfiles and give ownership to user pi, group emoncms

    $ sudo mkdir /var/log/rfm2pigateway
    $ sudo chown pi:emoncms /var/log/rfm2pigateway
    $ sudo chmod 750 /var/log/rfm2pigateway

  Make script run as daemon on startup

    $ sudo cp /var/www/emoncms/Modules/raspberrypi/rfm2pigateway.init.dist /etc/init.d/rfm2pigateway
    $ sudo chmod 755 /etc/init.d/rfm2pigateway
    $ update-rc.d rfm2pigateway defaults 99

  The gateway can be started or stopped anytime with following commands:
  
    $ sudo /etc/init.d/rfm2pigateway start
    $ sudo /etc/init.d/rfm2pigateway stop
    $ sudo /etc/init.d/rfm2pigateway restart
 
  To view the log:
    
    $ sudo tail -f -n 20 /var/log/rfm2pigateway/rfm2pigateway.log  (Ctrl+C to cancel)
    

