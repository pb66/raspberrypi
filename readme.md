#RFM12Pi interface module for emoncms

This module is to be used with an emoncms installation on a Raspberry Pi where you want to interface with an RFM12 to PI board.

For instructions on emoncms itself, check the repository [here](https://github.com/emoncms/emoncms)

##Features
- set the emoncms account to send data to
- set the RFM12 frequency
- set the RFM12 group
- set the RFM12 board node id.
- gateway scripts to forward data from serial port to local and remote emonCMS

##Installation

Install serial PHP libraries

    sudo apt-get install php-pear php5-dev
    sudo pecl install channel://pecl.php.net/dio-0.0.6
    sudo nano /etc/php5/cli/php.ini

add extension=dio.so to file in the beginning of the ;Dynamic Extensions; section on line 843 

[Ctrl+X] then [y] then [Enter] to save and exit

### Installation on Raspian/Debian/Ubuntu

It is possible to install this module using standard Debian package management. This
installation path involves fewer manual steps and controls for most dependency management 
automatically, and is therefore the recommended option if your system is compatible.

Note that you will need to install emoncms itself via the Debian repository in order to 
install modules in the same way.

Note that we maintain our own package `php5-dio` which will be automatically installed;
this should preclude you from having to use PEAR/PECL to install DIO. However, depending on your 
architecture the `php5-dio package` may not be suitable. Please feel free to build dio on your own
architecture and submit the deb to the package maintainer (dave@mccraw.co.uk) to resolve this.

    sudo apt-get update
    sudo apt-get install emoncms-module-rfm12pi

Configuration is done via the emoncms web interface. The `php5-dio`

### Manual Linux installation

Install serial PHP libraries

    sudo apt-get install php-pear php5-dev
    sudo pecl install channel://pecl.php.net/dio-0.0.6
    sudo nano /etc/php5/cli/php.ini

add extension=dio.so to file in the beginning of the ;Dynamic Extensions; section on line 843

[Ctrl+X] then [y] then [Enter] to save and exit

Clone the repository into the Modules/ directory of your emoncms installation.

Install rfm12piphp gateway service:

    sudo cp /var/www/emoncms/Modules/raspberrypi/rfm12piphp /etc/init.d/
    sudo chmod 755 /etc/init.d/rfm12piphp
    sudo update-rc.d rfm12piphp defaults

Start the service with:

    sudo /etc/init.d/rfm12piphp start
    
The following commands can also be used to control the service:

    sudo service rfm12piphp status
    sudo service rfm12piphp start
    sudo service rfm12piphp stop
    sudo service rfm12piphp restart

Important! You will need to re-run this installation procedure in full every time you pull new changes from github. If you do not re-copy the service script and restart it, your installation may suffer from impaired functionality.

#### Debugging

It is often useful to log the output of the rfm12piphp service to check that its working ok. Logging is turned off as default to reduce the amount of writes to an SD card-based installation. To turn logging on just add the word log to the end of the service command, ie:

    sudo service rfm12piphp restart log

To view the log:
    
    tail -F -n 40  /var/log/rfm12piphp.log

If running from SD, turn off logging when it's not needed to preserve your card's life, by calling restart without the 'log' argument:

    sudo service rfm12piphp restart
