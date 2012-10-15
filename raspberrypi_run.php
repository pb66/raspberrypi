<?php
  /*

  All Emoncms code is released under the GNU Affero General Public License.
  See COPYRIGHT.txt and LICENSE.txt.

  ---------------------------------------------------------------------
  Emoncms - open source energy visualisation
  Part of the OpenEnergyMonitor project:
  http://openenergymonitor.org
 
  */

  define('EMONCMS_EXEC', 1);

  $fp = fopen("importlock", "w");
  if (! flock($fp, LOCK_EX | LOCK_NB)) { echo "Already running\n"; die; }

  require("../../settings.php");
  include "../../db.php";
  db_connect();

  include "raspberrypi_model.php";
  raspberrypi_running();

  $settings = raspberrypi_get();
  $apikey = $settings['apikey'];
  $group = $settings['sgroup'];
  $frequency = $settings['frequency'];
  $baseid = $settings['baseid'];
  

  // Create a stream context that configures the serial port
  // And enables canonical input.
  $c = stream_context_create(array('dio' => 
    array('data_rate' => 9600, 
          'data_bits' => 8, 
          'stop_bits' => 1, 
          'parity' => 0, 
          'flow_control' => 0,
          'is_canonical' => 1)));

  // Are we POSIX or Windows?  POSIX platforms do not have a
  // Standard port naming scheme so it could be /dev/ttyUSB0
  // or some long /dev/tty.serial_port_name_thingy on OSX.
  if (PATH_SEPARATOR != ";") {
    $filename = "dio.serial:///dev/ttyAMA0";
  } else {
    $filename = "dio.serial://dev/ttyAMA0";
  }
 
  // Open the stream for read and write and use it.
  $f = fopen($filename, "r+", false, $c);
  if ($f) 
  {
    //fprintf($f,"\r\n");
    sleep(1);
    fprintf($f,$baseid."i");
    sleep(1);
    fprintf($f,$frequency."b"); 
    sleep(1);
    fprintf($f,$group."g");
    sleep(1);

    $start = time();

    while(true)
    {
      if (time()-$start>10)
      {
        $start = time();

        $settings = raspberrypi_get();
        if ($settings['apikey'] !=$apikey) $apikey = $settings['apikey'];
        if ($settings['sgroup'] !=$group) {$group = $settings['sgroup']; fprintf($f,$group."g");}
        if ($settings['frequency'] !=$frequency) {$frequency = $settings['frequency']; fprintf($f,$frequency."b"); }
        if ($settings['baseid'] !=$baseid) {$baseid = $settings['baseid']; fprintf($f,$baseid."i");}

        raspberrypi_running();
      }


      $data = fgets($f);
      if ($data && $data!="\n")
      {
        echo "SERIAL RX:".$data;

        if ($data[0]!=">")
        {
          $values = explode(' ',$data);
          $msubs = "";
          for($i=2; $i<(count($values)-1); $i+=2){
            if ($i>2) $msubs .= ",";
            $msubs .= $values[$i] + $values[$i+1]*256;
          }
          echo $msubs."\n";
          $url = "http://127.0.0.1/emoncms/input/post?apikey=".$apikey."&node=".$values[1]."&csv=".$msubs;
          $fh = @fopen($url, 'r' ); fclose($fh);
        }
      }

      usleep(100);

    }
  }
  fclose($f);

?>
