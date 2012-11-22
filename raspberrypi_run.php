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

  chdir(dirname(__FILE__));

  require "../../settings.php";
  include "../../db.php";
  db_connect();

  include "raspberrypi_model.php";
  raspberrypi_running();

  $settings = raspberrypi_get();
  $apikey = $settings['apikey'];
  $group = $settings['sgroup'];
  $frequency = $settings['frequency'];
  $baseid = $settings['baseid'];

  $remotedomain = $settings['remotedomain'];
  $remoteapikey = $settings['remoteapikey'];

  $sent_to_remote = false;
  $result = file_get_contents("http://".$remotedomain."/time/local.json?apikey=".$remoteapikey);
  if ($result[0]=='t') {echo "Remote upload enabled - details correct \n"; $sent_to_remote = true; }

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
    $ni = 0; $remotedata = "[";
    $start_time = time();
    $remotetimer = time();

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

        // Forward data to remote emoncms

      }

      if (time()-$remotetimer>30 && $sent_to_remote == true)
      {
        $remotetimer = time();

        $remotedata .= "]";
        echo "Sending remote data";
        //echo $remotedata."\n";
        getcontent($remotedomain,80,"/input/bulk.json?apikey=".$remoteapikey."&data=".$remotedata);
        $ni = 0; $remotedata = "[";
        $start_time = time();
      }

      $data = fgets($f);
      if ($data && $data!="\n")
      {
        echo "SERIAL RX:".$data;

        if ($data[0]!=">")
        {
          $values = explode(' ',$data);
          if ($values && is_numeric($values[1]))
          {
            $msubs = "";
            for($i=2; $i<(count($values)-1); $i+=2){
              if ($i>2) $msubs .= ",";
              //$msubs .= $values[$i] + $values[$i+1]*256;
              $int16 = $values[$i] + $values[$i+1]*256;
              if ($int16>32768) $int16 = -65536 + $int16;
              $msubs .= $int16;
            }
            //echo $msubs."\n";
            $url = "/emoncms/input/post?apikey=".$apikey."&node=".$values[1]."&csv=".$msubs;
            getcontent("localhost",80,$url);

            if ($sent_to_remote == true)
            {
              if ($ni!=0) $remotedata .= ",";
              $td = intval(time() - $start_time);
              $remotedata .= '['.$td.','.$values[1].','.$msubs.']'; $ni++;
            }

          }
        }
      }

    }
  }
  fclose($f);

function getcontent($server, $port, $file)
{
   $cont = "";
   $ip = gethostbyname($server);
   $fp = fsockopen($ip, $port);
   if (!$fp)
   {
       return "Unknown";
   }
   else
   {
       $com = "GET $file HTTP/1.1\r\nAccept: */*\r\nAccept-Language: de-ch\r\nAccept-Encoding: gzip, deflate\r\nUser-Agent: Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.0)\r\nHost: $server:$port\r\nConnection: Keep-Alive\r\n\r\n";
       fputs($fp, $com);
/* Don't realy need to fetch output as it slows us down
       while (!feof($fp))
       {
           $cont .= fread($fp, 500);
       }
*/
       fclose($fp);
//       $cont = substr($cont, strpos($cont, "\r\n\r\n") + 4);
//       return $cont;
   }
}
?>
