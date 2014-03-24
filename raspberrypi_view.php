<?php
  /*

  All Emoncms code is released under the GNU Affero General Public License.
  See COPYRIGHT.txt and LICENSE.txt.

  ---------------------------------------------------------------------
  Emoncms - open source energy visualisation
  Part of the OpenEnergyMonitor project:
  http://openenergymonitor.org
 
  */

  global $path, $user; 
?>

<script type="text/javascript" src="<?php echo $path; ?>Modules/raspberrypi/raspberrypi.js"></script>


<!-- Please preserve formatting (or edit debian/postinst to match). 
  This helps the forum offer technical support... -->
<div style="float:right; font-size:80%; font-style:italic">
Module version: 1.0
</div>


<div style="clear:right; float:right;"><a href="api">RaspberryPi API Help</a></div>
<br/>
<h2>Raspberry Pi</h2>
<h3>RFM12Pi interface</h3>

<div id="running" class="alert alert-success hide">
  RFM12 to Pi interface script is up and running
</div>

<div id="not-running"  class="alert alert-important hide">
  No data has been recieved from the RFM12Pi in the last 30s. Check if the Pi interface script is running, if not you may need to configure cron
</div>

<form id="testform">
  <div style="width:400px; float:left;">
    <p><b>Raspberry Pi connected to emoncms user account: <?php echo ""; $user->get_username($settings->userid); ?></b></p>

    <p>Select frequency to match RFM12B module:</p>
    <p>
    <input style="margin-bottom:6px;" type="radio" name="frequency" value="4" <?php if ($settings->frequency==4) echo "checked"; ?> > 433Mhz &nbsp; &nbsp;
    <input style="margin-bottom:6px;" type="radio" name="frequency" value="8" <?php if ($settings->frequency==8) echo "checked"; ?> > 868Mhz &nbsp; &nbsp;
    <input style="margin-bottom:6px;" type="radio" name="frequency" value="9" <?php if ($settings->frequency==9) echo "checked"; ?> > 915Mhz
    </p>

    <p>Network Group: (210 default, 1-212)<br><input type="text" name="sgroup" value="<?php echo $settings->sgroup; ?>" /></p>
    <p>RFM12Pi node ID: (15 default, 15-17)<br><input type="text" name="baseid" value="<?php echo $settings->baseid; ?>" /></p>
    <p><b>Broadcast time to synchronize emonGLCD</b></p>
    <p>Time sending interval (s): (default 0 = never)<br><input type="text" name="sendtimeinterval" value="<?php echo $settings->sendtimeinterval; ?>" /></p>
  </div>

  <div style="width:300px; float:left;" >
    <p><b>Forward data to remote emoncms server</b></p>

    <p>Protocol<br>
      <select name="remoteprotocol">
        <option value = "http://" <?php if($settings->remoteprotocol=="http://") echo "selected"; ?>>http://</option>
        <option value = "https://" <?php if($settings->remoteprotocol=="https://") echo "selected"; ?>>https://</option>
      </select>
    <p>Domain name<br><input type="text" name="remotedomain" value="<?php echo $settings->remotedomain; ?>" /></p>
    <p>Path to emoncms<br><input type="text" name="remotepath" value="<?php echo $settings->remotepath; ?>" /></p>
    <p>Write apikey<br><input type="text" name="remoteapikey" value="<?php echo $settings->remoteapikey; ?>" /></p>

    <div id="remotesend-true" class="alert alert-success hide" >Authentication successful</div>
    <div id="remotesend-false" class="alert alert-error hide">Incorrect remote server details</div>

  </div>
</form>

<div style="padding-top:10px; width:110px;">
  <button id="save-button" class="btn" >Save</button>
  <div id="saved" style="display:none; float:right; color:#888; padding-top:6px">Saved</div>
</div>

<script>

  var path = "<?php echo $path; ?>";

  var settings = raspberrypi.get();
  // for (z in settings) console.log(settings[z]); 

  if (settings.remotesend==true) {
    $("#remotesend-true").show(); 
    $("#remotesend-false").hide();
  } else {
    $("#remotesend-true").hide(); 
    $("#remotesend-false").show(); 
  }

  setInterval(update, 5000);
  update();

  function update()
  {
    if (raspberrypi.getrunning()==true) {
      $("#running").show(); 
      $("#not-running").hide();
    } else {
      $("#running").hide(); 
      $("#not-running").show(); 
    }
  }

  $("#save-button").click(function(){

    var form = $('#testform').serializeArray();
    var fields = {}; for (z in form) fields[form[z].name] = form[z].value;
    var result = raspberrypi.set(fields);

    if (result.success == true) $("#saved").show();

    if (result.remotesend==true) {
      $("#remotesend-true").show(); 
      $("#remotesend-false").hide();
    } else {
      $("#remotesend-true").hide(); 
      $("#remotesend-false").show(); 
    }
  });

  $("input").keyup(function(){ $("#saved").hide(); });
  $("input[name=frequency]").click(function(){ $("#saved").hide(); });

</script>
