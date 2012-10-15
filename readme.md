#Raspberry PI emoncms module

This module is to be used with an emoncms installed on the PI to interface with an RFM12 to PI board in a seemless fashion.

##Features:
- set the emoncms account to send data to
- set the RFM12 frequency
- set the RFM12 group
- set the RFM12 board node id.
- php serial script

##Requires the pecl php serial module

sudo apt-get install php-pear php5-dev
sudo pecl install channel://pecl.php.net/dio-0.0.6
Add "extension=dio.so" to php.ini
Restart apache
