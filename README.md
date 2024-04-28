# SMTP_mail_for_Frigate
myFrigateMail.py receives and mails snapshots and clips which are published by Frigate on MQTT


Python program myFrigateMail.py receives and mails snapshots and clips which are published by Frigate on MQTT

Adapt in the Python program the variables marked between these comment lines:
-----------------------------------------------------------------------------
### START OF: YOU MUST SET THE REQUIRED VARIABLES TO YOUR NEEDS!!
### END OF: YOU MUST SET THE REQUIRED VARIABLES TO YOUR NEEDS!!

Suggested input the config.yml of Frigate.
------------------------------------------
 
#
# The following mqtt, motion and cameras part(s) were set in the config.yml of Frigate to support MQTT
# you can copy and adapt if you want to
#
#    mqtt:
#      enabled: true
#      host: 192.168.2.5
#      port: 1883
#      topic_prefix: frigate
#      client_id: frigate
#      password: keep_that_secret
#      stats_interval: 60
#
#    motion:
#      # other parameters as well
#      mqtt_off_delay: 30
#
#    cameras:
#      tapo_camera: # <--- this will be changed to your actual camera later
#        detect:
#          enabled: true # <---- disable detection until you have a working camera feed
#        record:
#          enabled: true # <---- disable recording until you have a working camera feed
#        snapshots: # <----- Enable snapshots
#          enabled: true
#        zones:
#          # more parameters were used here, not shown
#        mqtt:
#          enabled: true
#          timestamp: true
#          bounding_box: true
#          crop: False
#          height: 1440
#          quality: 100
#          required_zones: []

Make a Service that automatically starts/stops this program during startup/stop of your linux server
----------------------------------------------------------------------------------------------------
The file FrigateMail_example.service contains a the service definition to run this mail program automatically

Change it to your needs (check the path names!!)
Save it as FrigateMail.service
Install this service with:
 sudo cp /home/<user>/Documents/MyScripts/FrigateMail.service /lib/systemd/system/
 sudo systemctl enable FrigateMail.service
 sudo systemctl start FrigateMail.service
 # check and reboot when needed or use Cockpit, see https://www.stephenwagner.com/2020/03/21/raspberry-pi-4-handy-tips-tricks-commands/
 sudo systemctl list-unit-files

