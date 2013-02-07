<?php
  /*

  All Emoncms code is released under the GNU Affero General Public License.
  See COPYRIGHT.txt and LICENSE.txt.

  ---------------------------------------------------------------------
  Emoncms - open source energy visualisation
  Part of the OpenEnergyMonitor project:
  http://openenergymonitor.org
 
  */

  // no direct access
  defined('EMONCMS_EXEC') or die('Restricted access');

  function raspberrypi_controller()
  {
    include "Modules/raspberrypi/raspberrypi_model.php";
    global $session, $route;

    $format = $route['format'];
    $action = $route['action'];

    $output['content'] = "";
    $output['message'] = "";

    if ($action == "view" && $session['write'])
    { 
      $settings = raspberrypi_get();
      if ($format == 'html') $output['content'] = view("raspberrypi/raspberrypi_view.php", array('settings'=>$settings));
       if ((time()-$settings['running'])<30) 
         $output['message'] = array('success',"RFM12 to PI interface script is up and running");
       else
         $output['message'] = array('important',"No data has been recieved from the RFM12PI in the last 30s. Check if the PI interface script is running, if not you may need to configure cron");
    }

    if ($action == "set" && $session['write'])
    { 
      $userid = $session['userid'];
      $apikey = get_apikey_write($userid);
      $sgroup = intval(get('sgroup'));
      $frequency = intval(get('frequency'));
      $baseid = intval(get('baseid'));
      $remotedomain = urldecode(get('remotedomain'));
      $remotepath = get('remotepath');
      if($remotepath[0]!='/') {$remotepath='/'.$remotepath;} // ensure leading slash in remotepath
      $remoteapikey = db_real_escape_string(preg_replace('/[^.\/A-Za-z0-9]/', '', get('remoteapikey')));

      $remotesend = false;
      if ($remotedomain && $remoteapikey && $remotepath) {
        $result = file_get_contents("http://".$remotedomain.$remotepath."/time/local.json?apikey=".$remoteapikey); 
        if ($result[0]=='t') $remotesend = true;
      }

      raspberrypi_set($userid,$apikey,$sgroup,$frequency,$baseid,$remotedomain,$remotepath,$remoteapikey,$remotesend);

      $output['message'] = "Raspberry PI settings updated"; 
    }

    return $output;
  }

?>
