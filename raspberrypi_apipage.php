<?php global $path, $session, $user; ?>

<h2>RaspberryPI API</h2>

<h3>Apikey authentication</h3>
<p>If you want to call any of the following action's when your not logged in, add an apikey to the URL of your request: &apikey=APIKEY.</p>
<p><b>Read only:</b><br>
<input type="text" style="width:230px" readonly="readonly" value="<?php echo $user->get_apikey_read($session['userid']); ?>" />
</p>

<p><b>Read & Write:</b><br>
<input type="text" style="width:230px" readonly="readonly" value="<?php echo $user->get_apikey_write($session['userid']); ?>" />
</p>

<h3>Html</h3>
<p><a href="<?php echo $path; ?>raspberrypi/config"><?php echo $path; ?>raspberrypi/config</a> - RaspberryPI config page</p>
<p><a href="<?php echo $path; ?>raspberrypi/api"><?php echo $path; ?>raspberrypi/api</a> - this page</p>

<h3>JSON</h3>
<p>To use the json api the request url needs to include .json</p>

<p><b>Set settings</b></p>
<p><a href="<?php echo $path; ?>raspberrypi/set.json?fields={'sgroup':210,'frequency':4,'baseid':15,'remoteprotocol':'http://','remotedomain':'emoncms.org','remotepath':'/','remoteapikey':'REMOTE_APIKEY','sendtimeinterval':0}"><?php echo $path; ?>raspberrypi/set.json?fields=<br>{'sgroup':210,'frequency':4,'baseid':15,'remoteprotocol':'http://','remotedomain':'emoncms.org','remotepath':'/','remoteapikey':'REMOTE_APIKEY','sendtimeinterval':0}</a><br>returns confirmation if settings given for remote server are correct. Requires write apikey.</p>

<p><b>Get settings</b></p>
<p><a href="<?php echo $path; ?>raspberrypi/get.json"><?php echo $path; ?>raspberrypi/get.json</a> - returns raspberrypi settings. Requires read apikey <b>OR a request from localhost</b></p>

<p><b>Check if run script is running</b></p>
<p><a href="<?php echo $path; ?>raspberrypi/getrunning.json"><?php echo $path; ?>raspberrypi/getrunning.json</a> - returns true if raspberrypi_run script is running. Requires read apikey.</p>

<p><b>Inform EmonCMS that run script is running</b></p>
<p><a href="<?php echo $path; ?>raspberrypi/setrunning.json"><?php echo $path; ?>raspberrypi/setrunning.json</a> - returns Null. Requires write apikey <b>OR a request from localhost</b>.</p>

