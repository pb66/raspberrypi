
var raspberrypi = {

  'get':function()
  {
    var result = {};
    $.ajax({ url: path+"raspberrypi/get.json", dataType: 'json', async: false, success: function(data){result = data;} });
    return result;
  },

  'set':function(fields)
  {
    var result = {};
    // sgroup= &frequency= &baseid= &remotedomain= &remotepath= &remoteapikey=
    $.ajax({ url: path+"raspberrypi/set.json", data: "fields="+JSON.stringify(fields), dataType: 'json', async: false, success: function(data){result = data;} });
    return result;
  },

  'getrunning':function()
  {
    var result = {};
    $.ajax({ url: path+"raspberrypi/getrunning.json", dataType: 'json', async: false, success: function(data) {result = data;} });
    return result;
  },

  'setrunning':function()
  {
    var result = {};
    $.ajax({ url: path+"raspberrypi/setrunning.json", dataType: 'json', async: false, success: function(data) {result = data;} });
    return result;
  }

}

