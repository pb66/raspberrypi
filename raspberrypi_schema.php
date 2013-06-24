<?php

$schema['raspberrypi'] = array(
  'userid' => array('type' => 'int(11)'),
  'apikey' => array('type' => 'text'),
  'sgroup' => array('type' => 'int(11)'),
  'frequency' => array('type' => 'int(11)'),
  'baseid' => array('type' => 'int(11)'),
  'running' => array('type' => 'int(11)'),
  'remotedomain' => array('type' => 'text'),
  'remoteprotocol' => array('type' => 'text'),
  'remotepath' => array('type' => 'text'),
  'remoteapikey' => array('type' => 'text'),
  'remotesend' => array('type' => 'int(11)'),
  'sendtimeinterval' => array('type' => 'int(11)', 'default'=>0)
);

?>
