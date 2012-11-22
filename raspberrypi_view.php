<?php
  /*

  All Emoncms code is released under the GNU Affero General Public License.
  See COPYRIGHT.txt and LICENSE.txt.

  ---------------------------------------------------------------------
  Emoncms - open source energy visualisation
  Part of the OpenEnergyMonitor project:
  http://openenergymonitor.org
 
  */

  $sent_to_remote = false;
  $result = file_get_contents("http://".$settings['remotedomain']."/time/local.json?apikey=".$settings['remoteapikey']);
  if ($result[0]=='t') $sent_to_remote = true;

?>

<h2>Raspberry PI</h2>

<div style="width:400px; float:left;">
<form action="set" method="GET" >
<p><b>Raspberry Pi connected to account: <?php echo get_user_name($settings['userid']); ?></b></p>

<p>Select your RFM12 Frequency:</p>
<p>
<input style="margin-bottom:6px;" type="radio" name="frequency" value="4" <?php if ($settings['frequency']==4) echo "checked" ?> > 433Mhz &nbsp; &nbsp;
<input style="margin-bottom:6px;" type="radio" name="frequency" value="8" <?php if ($settings['frequency']==8) echo "checked" ?> > 868Mhz &nbsp; &nbsp;
<input style="margin-bottom:6px;" type="radio" name="frequency" value="9" <?php if ($settings['frequency']==9) echo "checked" ?> > 915Mhz
</p>

<p>Group: (0=any,0-212)<br><input type="text" name="sgroup" value="<?php echo $settings['sgroup']; ?>" /></p>
<p>Base ID: (1-26)<br><input type="text" name="baseid" value="<?php echo $settings['baseid']; ?>" /></p>

<br><input type="submit" class="btn" value="Save" />

</div>

<div style="width:400px; float:left;" >
<p><b>Forward data to remote emoncms</b></p>

<p>Domain name<br><input type="text" name="remotedomain" value="<?php echo $settings['remotedomain']; ?>" /></p>
<p>Write apikey<br><input type="text" name="remoteapikey" value="<?php echo $settings['remoteapikey']; ?>" /></p>
<?php if ($send_to_remote) echo "<p><b>Authentication successful</b></p>"; ?>

</form>
</div>
