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

class RaspberryPI
{
    private $mysqli;

    public function __construct($mysqli)
    {
        $this->mysqli = $mysqli;
    }

    public function get()
    {
        $result = $this->mysqli->query("SELECT * FROM raspberrypi");
        $row = $result->fetch_object();
       
        if ($result->num_rows==0)
        {
            $this->mysqli->query("INSERT INTO raspberrypi ( userid, apikey, sgroup ,frequency, baseid, remotedomain, remoteprotocol, remotepath, remoteapikey, remotesend, sendtimeinterval) VALUES ( '0' , '' ,'1','4','15' ,'emoncms.org','http://','/','YOURAPIKEY','false','0');");
            $result = $this->mysqli->query("SELECT * FROM raspberrypi");
            $row = $result->fetch_object();
        }
        return $row;
    }

    public function set($userid,$apikey,$fields)
    {
        $fields = json_decode($fields);

        $remotesend = false;
        if (isset($fields->remoteprotocol) && isset($fields->remotedomain) && isset($fields->remoteapikey) && isset($fields->remotepath)) {
            $result = file_get_contents($fields->remoteprotocol.$fields->remotedomain.$fields->remotepath."/time/local.json?apikey=".$fields->remoteapikey); 
            if (isset($result[0]) && $result[0]=='t') $remotesend = true;
        }

        $array = array();

        $array[] = "`userid` = '".$userid."'";
        $array[] = "`apikey` = '".$apikey."'";
        $array[] = "`remotesend` = '".$remotesend."'";

        // Repeat this line changing the field name to add fields that can be updated:
        if (isset($fields->sgroup)) $array[] = "`sgroup` = '".intval($fields->sgroup)."'";
        if (isset($fields->frequency)) $array[] = "`frequency` = '".intval($fields->frequency)."'";
        if (isset($fields->baseid)) $array[] = "`baseid` = '".intval($fields->baseid)."'";
        if (isset($fields->remotedomain)) $array[] = "`remotedomain` = '".urldecode($fields->remotedomain)."'";

        if (isset($fields->remoteprotocol)) $array[] = "`remoteprotocol` = '".$fields->remoteprotocol."'";

        if (isset($fields->remotepath)) {
          // ensure leading slash in remotepath
          if($fields->remotepath[0]!='/') {$fields->remotepath='/'.$fields->remotepath;}  
          $array[] = "`remotepath` = '".$fields->remotepath."'";
        }

        if (isset($fields->remoteapikey)) $array[] = "`remoteapikey` = '".($this->mysqli->real_escape_string(preg_replace('/[^.\/A-Za-z0-9]/', '', $fields->remoteapikey)))."'";
        
        if (isset($fields->sendtimeinterval)) $array[] = "`sendtimeinterval` = '".intval($fields->sendtimeinterval)."'";

        // Convert to a comma seperated string for the mysql query
        $fieldstr = implode(",",$array);
        $this->mysqli->query("UPDATE raspberrypi SET ".$fieldstr);

        return array('success'=>true, 'message'=>'Field updated', 'remotesend'=>$remotesend);
    }

    public function set_running()
    { 
        $time = time();
        $this->mysqli->query("UPDATE raspberrypi SET `running` = '$time' ");
    }

    public function get_running()
    { 
        $result = $this->mysqli->query("SELECT running FROM raspberrypi");
        $row = $result->fetch_object();
        if ((time()-$row->running)<30) return true; else return false;
    }
}
?>
