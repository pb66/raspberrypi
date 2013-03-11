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
  
  include "raspberrypi_model.php";
  include "../../settings.php";
  include "../../db.php";

  function get($index)
  {
    $val = null;
  
    if (isset($_GET[$index])) $val = $_GET[$index];
  
    return $val;
  }

  # Only accept requests from localhost
  if($_SERVER['REMOTE_ADDR']=='127.0.0.1')
  {
    # Request can be...
    switch (get('action'))
    {
      # Gateway parameters
      case 'params':
        db_connect();
        $settings = raspberrypi_get();
        foreach ($settings as $key => $value)
        {
            echo "$key:$value\n";
        }
        break;
      
      # Update "running" status
      case 'running':
        db_connect();
        raspberrypi_running();
        break;
      
      # What else ? (TM)
      default:
        echo 'WTF ?';
    }
  } 
  else
  {
  echo "Restricted access";
  }
?>

