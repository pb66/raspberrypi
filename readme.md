#Raspberry PI emoncms module

This module is to be used with an emoncms installed on the PI to interface with an RFM12 to PI board in a seemless fashion.

##Features
- set the emoncms account to send data to
- set the RFM12 frequency
- set the RFM12 group
- set the RFM12 board node id.
- gateway scripts to forward data from serial port to local and remote emonCMS

##Installation

Install one of the two available gateway scripts to let them run on startup

### Raspberry_run.php (currently has stability issue with sending time to EmonGLCD, see python script for alternative)

  Install pecl php serial module

    $ sudo apt-get install php-pear php5-dev
    $ sudo pecl install channel://pecl.php.net/dio-0.0.6

  Open php.ini with nano or any other editor and add "extension=dio.so"
  in the beginning of the ;Dynamic Extensions; section

    $ sudo nano /etc/php5/cli/php.ini

  Open crontab with nano or any other editor

    $ sudo nano /etc/crontab

  Add following line at the end of the file:

  */1 * * * * root cd /var/www/emoncms/Modules/raspberrypi && php raspberrypi_run.php

  Then reboot. The script will be run every minute after startup.

    $ sudo reboot

### RFM2Pi Gateway (python script)

  Install python serial port and mySQL modules

    $ sudo aptitude install python-serial python-mysqldb
  
  Create groupe emoncms and make user pi part of it

    $ sudo groupadd emoncms
    $ usermod -a -G emoncms pi

  Create a directory for the logfiles and give ownership to user pi, group emoncms

    $ sudo mkdir /var/log/rfm2pigateway
    $ sudo chown pi:emoncms /var/log/rfm2pigateway
    $ sudo chmod 750 /var/log/rfm2pigateway

  Make apache user part of emoncms group, to read log files
    
    $ usermod -a -G emoncms www-data

  Give apache the possibility to start/stop the gateway
    
    $ sudo cp rfm2pigateway.sudoers.dist /etc/sudoers.d/rfm2pigateway
    $ sudo chmod 440 /etc/sudoers.d/rfm2pigateway

  Make script run as daemon on startup

    $ sudo cp rfm2pigateway.init.dist /etc/init.d/rfm2pigateway
    $ sudo chmod 755 /etc/init.d/rfm2pigateway
    $ update-rc.d rfm2pigateway defaults 99

  The gateway can be started or stopped anytime with following commands:

    $ sudo /etc/init.d/rfm2pigateway start
    $ sudo /etc/init.d/rfm2pigateway stop
    $ sudo /etc/init.d/rfm2pigateway restart
    
  To view the log:
    
    $ tail -F -n 40  /var/log/rfm2pigateway/rfm2pigateway.log

