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

  class ProcessArg {
    const VALUE = 0;
    const INPUTID = 1;
    const FEEDID = 2;
  }

  class DataType {
    const UNDEFINED = 0;
    const REALTIME = 1;
    const DAILY = 2;
    const HISTOGRAM = 3;
  }

  require "../../settings.php";
  include "../../db.php";
  db_connect();

  include "raspberrypi_model.php";
  include "../user/user_model.php";
  include "../input/input_model.php";
  include "../input/process_model.php";
  raspberrypi_running();

  $settings = raspberrypi_get();
  $apikey = $settings['apikey'];
  $userid = get_apikey_write_user($apikey);
  if ($userid == 0) $userid = 1;

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
        if ($settings['apikey'] !=$apikey) {
          $apikey = $settings['apikey'];
          $userid = get_apikey_write_user($apikey);
        }
        if ($settings['sgroup'] !=$group) {$group = $settings['sgroup']; fprintf($f,$group."g");}
        if ($settings['frequency'] !=$frequency) {$frequency = $settings['frequency']; fprintf($f,$frequency."b"); }
        if ($settings['baseid'] !=$baseid) {$baseid = $settings['baseid']; fprintf($f,$baseid."i");}

        if ($settings['remotedomain'] !=$remotedomain || $settings['remoteapikey'] !=$remoteapikey)
        { 
          $result = file_get_contents("http://".$remotedomain."/time/local.json?apikey=".$remoteapikey);
          if ($result[0]=='t') {echo "Remote upload enabled - details correct \n"; $sent_to_remote = true; }
        }

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
            $node = $values[1];
            $msubs = "";
            $id = 1;

            $inputs = array();

            for($i=2; $i<(count($values)-1); $i+=2){
              if ($i>2) $msubs .= ",";

              // Each iteration here is a input value
              // The RFM12b data is recieved and forwarded here as number string
              // each number corresponds to a 8-bit byte of rfm12b data
              // We start by getting the 16-bit integers by combining 2 8-bit numbers.

              // Get 16-bit integer
              $int16 = $values[$i] + $values[$i+1]*256;
              if ($int16>32768) $int16 = -65536 + $int16;
              $msubs .= $int16;
              $value = $int16;

              // Next we set the time that the packet was recieved
              $time = time();

              // Create multinode type input name
              // We're using the multinode input name convention
              // which is of the form node10_1, node10_2
              $name = "node".$node.'_'.$id;

              // Check if input exists and get its id
              $id = get_input_id($userid,$name);

              if ($id==0) {
                // If the input does not exist then create it
                $id = create_input_timevalue($userid,$name,$node,$time,$value);
              } else {	
                // If it does exist then set the timevalue			
                set_input_timevalue($id,$time,$value);
              }
              // Put in input list ready for processing
              $inputs[] = array('id'=>$id,'time'=>$time,'value'=>$value);
              $id++;
            }

            // Run the input processor (new to call new version of the input processor..)
            new_process_inputs($userid,$inputs);

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
