<?php
  /*

  All Emoncms code is released under the GNU Affero General Public License.
  See COPYRIGHT.txt and LICENSE.txt.

  ---------------------------------------------------------------------
  Emoncms - open source energy visualisation
  Part of the OpenEnergyMonitor project:
  http://openenergymonitor.org
 
  */

?>

<h2>Raspberry PI</h2>

<div style="width:400px; float:left;">
<form action="set" method="GET" >
<p><b>Raspberry Pi connected to emoncms user account: <?php echo get_user_name($settings['userid']); ?></b></p>

<p>Select frequency to match RFM12B module:</p>
<p>
<input style="margin-bottom:6px;" type="radio" name="frequency" value="4" <?php if ($settings['frequency']==4) echo "checked" ?> > 433Mhz &nbsp; &nbsp;
<input style="margin-bottom:6px;" type="radio" name="frequency" value="8" <?php if ($settings['frequency']==8) echo "checked" ?> > 868Mhz &nbsp; &nbsp;
<input style="margin-bottom:6px;" type="radio" name="frequency" value="9" <?php if ($settings['frequency']==9) echo "checked" ?> > 915Mhz
</p>

<p>Network Group: (210 default, 1-212)<br><input type="text" name="sgroup" value="<?php echo $settings['sgroup']; ?>" /></p>
<p>RFM12Pi node ID: (15 default, 15-17)<br><input type="text" name="baseid" value="<?php echo $settings['baseid']; ?>" /></p>

<br><input type="submit" class="btn" value="Save" />

</div>

<div style="width:400px; float:left;" >
<p><b>Forward data to remote emoncms server</b></p>

<p>Domain name<br><input type="text" name="remotedomain" value="<?php echo $settings['remotedomain']; ?>" /></p>
<p>Write apikey<br><input type="text" name="remoteapikey" value="<?php echo $settings['remoteapikey']; ?>" /></p>
<?php if ($settings['remotesend']) echo "<p><b>Authentication successful</b></p>"; else echo "<p><b>Incorrect remote server details</b></p>"; ?>

</form>
</div>
