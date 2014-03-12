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
    global $mysqli, $session, $route, $user;

    include "Modules/raspberrypi/raspberrypi_model.php";
    $raspberrypi = new RaspberryPI($mysqli);

    $result = false;

    // html views
    if ($route->format == 'html')
    {
        if ($route->action == "config" && $session['write']) $result = view("Modules/raspberrypi/raspberrypi_view.php", array('settings'=>$raspberrypi->get()));
        if ($route->action == "api" && $session['write']) $result = view("Modules/raspberrypi/raspberrypi_apipage.php", array());
    }

    // JSON api
    if ($route->format == 'json')
    {
        if ($route->action == "set" && $session['write']) $result = $raspberrypi->set($session['userid'],$user->get_apikey_write($session['userid']),get('fields'));
        if ($route->action == "get" && ($session['read'] || $_SERVER['REMOTE_ADDR'] == $_SERVER['SERVER_ADDR'])) $result = $raspberrypi->get();
        if ($route->action == "setrunning" && ($session['write'] || $_SERVER['REMOTE_ADDR'] == $_SERVER['SERVER_ADDR'])) $result = $raspberrypi->set_running();
        if ($route->action == "getrunning" && $session['read']) $result = $raspberrypi->get_running();
    }

    return array('content'=>$result);
}

?>
