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
</form>
