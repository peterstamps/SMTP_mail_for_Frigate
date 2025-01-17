# This program receives and mails snapshots and clips which are published by Frigate
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

        
import json
import requests
import datetime

import smtplib
from pathlib import Path
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.utils import COMMASPACE, formatdate
from email import encoders

import paho.mqtt.client as mqtt
import ssl
from datetime import datetime as dt

import os
from collections import deque


# START VARIABLES 
q = deque() # to get the mqtt messages

### START OF: YOU MUST SET THE REQUIRED VARIABLES TO YOUR NEEDS!!

# For Frigate host_ip and port   
frigate_host_ip = '192.168.2.5'   # your IP address of the server where frigate runs and listens to!
frigate_http_port = "5000"        # the default frigate port for its web server nginx
objects_to_look_for = ('person', 'dog', 'cat')  # MUST be inside the round brackets like this ('person', 'car')
object_storage_path = '/home/<user>/Videos/Tapo/' # MUST end with endslash! Change <user> or whole path!
#
# For MQTT
mqttclient_id = "clientid123"
mqttusername = "<yourname>"   # your name or leave empty 
mqttpassword = "<yourpassword>"   # your password or leave empty 
mqtthost_ip = "192.168.2.5" # your IP address of the server where MQTT runs and listens to!
mqttport = 1883  # default port 1883
mqttsslport = 8883 # default ssl port8883
mqttuse_ssl = False   # Set to True if you want to use ssl (check also the configuration of Frigate in that case!)
mqttca_cert = "/home/<user>/Documents/MyCertificates/ca-crt.pem"   # ca-certificate is required when using ssl (mqttuse_ssl = True)
mqtttopic = "frigate/events"  # the default settings used by Frigate, can be any setting (check also the configuration of Frigate in that case!)
#mqtttopic = "frigate/+"  # alternative setting, just as example or for test purposes

# For SMTP email
emailusername = '<mailadrress of account>' # Your full email address of your account at your mail provider
emailpassword = '<password of account>' # your password of your account at your mail provider>'
emailserver = "smtp.gmail.com" # examples smtp.gmail.com, mail.kpnmal.nl, 
emailport = 587 # smtp port, test first with this port and change only if your provider requires that or you know whihc port must be set
emailTo =  '<mail to address>'  # to which emnail address should the mail be send
emailFrom = '<mail comes from address/name>'  # email addres/name of who sends this mail
emailtitel =  'Frigate event @ '  # a formatted date (YYY-MM-DD HH:MM:DD will automatically be added after this string so here after the @ and the space 
emailbody_text = 'A video/snapshot is recorded by Frigate surveillance' # will be added in the body text of the mail. Use \n to get a line break. E.g. "Test Line\nTestLine2\n"
email_maximum_size = 50000000  # MUST be in bytes  (so 5GB is defined here)

### END OF: YOU MUST SET THE REQUIRED VARIABLES TO YOUR NEEDS!!

emailfiles = []  # do not change this
emailuse_tls = True # do not change this

# END VARIABLES 

def send_mail(send_from, send_to, subject, message, files, server, port, username, password, use_tls, object_storage_path): 
    """Compose and send email with provided info and attachments.
    Args:
        send_from (str): from name
        send_to (list[str]): to name(s)
        subject (str): message title
        message (str): message body
        files (list[str]): list of file paths to be attached to email
        server (str): mail server host name
        port (int): port number
        username (str): server auth username
        password (str): server auth password
        use_tls (bool): use TLS mode
    """
    msg = MIMEMultipart()
    msg['From'] = send_from
    msg['To'] = COMMASPACE.join(send_to)
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = subject + dt.now().strftime('%Y-%m-%d %H:%M:%S')

    msg.attach(MIMEText(message))
    for path in files:
        part = MIMEBase('Content-Type', "application/octet-stream") 
        if path.endswith('.mp4'):
          part = MIMEBase('Content-Type', "video/mp4")            
        if path.endswith('.jpg'):  
          part = MIMEBase('Content-Type', "image/jpg")  
        try:
          with open(object_storage_path+path, 'rb') as file:
              part.set_payload(file.read())
          encoders.encode_base64(part)
          part.add_header('Content-Disposition',
                          'attachment; filename={}'.format(Path(path).name))
          msg.attach(part)
          if path.endswith('.mp4'):
            msg.attach(MIMEText("\nVideo filename: " + path)) 
          if path.endswith('.jpg'):
            msg.attach(MIMEText("\nPicture filename: " + path)) 
        except:
          print(f"{dt.now().strftime('%Y-%m-%d %H:%M:%S')} Error with attachment, skipping {object_storage_path+path}")
          pass

    try:
      smtp = smtplib.SMTP(server, port)
      if use_tls:
          smtp.starttls()
      smtp.login(username, password)
      smtp.sendmail(send_from, send_to, msg.as_string())
      smtp.quit()
      return 'ok'
    except smtplib.SMTPSenderRefused as exc:
      print(f"{dt.now().strftime('%Y-%m-%d %H:%M:%S')} error sending:\n", exc.sender)
    except smtplib.SMTPDataError:
      print(f"{dt.now().strftime('%Y-%m-%d %H:%M:%S')} Message is too big, the size is {msg.as_string()}")
    return 'nok'
    

def findkeys(node, kv):
    if isinstance(node, list):
        for i in node:
            for x in findkeys(i, kv):
               yield x
    elif isinstance(node, dict):
        if kv in node:
            yield node[kv]
        for j in node.values():
            for x in findkeys(j, kv):
                yield x
  # print(list(findkeys(data, 'label')))   


def get_Frigate_obj(data, frigate_host_ip, frigate_http_port, object_storage_path):
  if data.get('type'):  # type can contain "new", "update" and "end"
    if "end" in data["type"]:  # we need to get type: end to get a full clip and not a clip in progress
      if data.get('before'):
        if data.get('before').get('label'):    
          #for value in findkeys(data, 'label'):
          #    print(value)
#          if 'person' in data['before']['label'] or 'car' in data['before']['label'] :
          if data['before']['label'] in objects_to_look_for:
            event_id=data['before']['id']
            start_url = f"http://{frigate_host_ip}:{frigate_http_port}/api/events/"
            
            urlClip = f"{start_url}{event_id}/clip.mp4"
            urlSnapshot = f"{start_url}{event_id}/snapshot.jpg"

            filenameClip = 'no clip' # will be overwritten when clip exists
            filenameSnapshot = 'no snapshot' # will be overwritten when thumbnail exists
            filesizeClip = filesizeThumbnail = filesizeSnapshot = 0            
            
            if data.get('before').get('has_clip'):
              if data['before']['has_clip'] == True: 
                start_time = datetime.datetime.fromtimestamp( data['before']['start_time']).strftime("%Y_%m_%d_%H_%M_%S")
                filenameClip=f"c_{start_time}.mp4"
                res = requests.get(urlClip)
                if res.status_code == 200:
                    with open(object_storage_path+filenameClip,'wb') as f:
                        f.write(res.content)
                        f.seek(0, os.SEEK_END)
                        filesizeClip = f.tell()
                        #f.seek(0, os.SEEK_SET)  # back to the start
                        print(f"{dt.now().strftime('%Y-%m-%d %H:%M:%S')} File {object_storage_path+filenameClip} has {filesizeClip} bytes")

            if data.get('before').get('has_snapshot'):
              if data['before']['has_snapshot'] == True:    
                start_time = datetime.datetime.fromtimestamp( data['before']['start_time']).strftime("%Y_%m_%d_%H_%M_%S")
                filenameSnapshot=f"s_{start_time}.jpg"
                res = requests.get(urlSnapshot)
                if res.status_code == 200:
                    with open(object_storage_path+filenameSnapshot,'wb') as f:
                        f.write(res.content)
                        f.seek(0, os.SEEK_END)
                        filesizeSnapshot = f.tell()
                        #f.seek(0, os.SEEK_SET) # back to start
                        print(f"{dt.now().strftime('%Y-%m-%d %H:%M:%S')} File {object_storage_path+filenameSnapshot} has {filesizeSnapshot} bytes")

                                    
            return (filenameClip, filesizeClip,  urlClip, filenameSnapshot, filesizeSnapshot, urlSnapshot)
                  
  return ('no clip', 0, 'no clip url', 'no snapshot', 0, "no snapshot url")


def on_subscribe(client, userdata, mid, qos, properties=None):
    print(f"{dt.now().strftime('%Y-%m-%d %H:%M:%S')} Subscribed with {qos[0]}")
    
def on_connect(client, userdata, flags, reason_code, properties=None):
    print(f"{dt.now().strftime('%Y-%m-%d %H:%M:%S')} Connected with {str(reason_code)}")

def on_message(client, userdata, message, properties=None):
    print(
      f"{dt.now().strftime('%Y-%m-%d %H:%M:%S')} Received message on topic '{message.topic}' with QoS {message.qos}, length: {len(message.payload)}"
    )
    # parse json based message
    # the result is a Python dictionary
    try:
      data = ['json', json.loads(message.payload)]
    except:
      data = ['no json', message.payload]
    q.append(data)
    print(f"{dt.now().strftime('%Y-%m-%d %H:%M:%S')} Messages in deque: {len(q)}")


def processFrigateEventMessages(mqttclient_id, mqtttopic, mqttusername, mqttpassword, mqtthost_ip, 
      mqttport, mqttsslport, mqttuse_ssl, mqttca_cert, emailFrom, emailTo, emailtitel, 
      emailbody_text, emailserver, emailport, emailusername, emailpassword, emailuse_tls, email_maximum_size, object_storage_path):
      
      client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=mqttclient_id, protocol=mqtt.MQTTv5)
      client.username_pw_set(username=mqttusername, password=mqttpassword)

      client.on_subscribe = on_subscribe
      client.on_message = on_message
            
      if mqttuse_ssl == False:
        client.connect(mqtthost_ip,mqttport)
      else:
        client.connect(mqtthost_ip,mqttsslport)
        client.tls_set(ca_certs=mqttca_cert, cert_reqs=ssl.CERT_NONE)
        client.tls_insecure_set(True)
        
      print(f"{dt.now().strftime('%Y-%m-%d %H:%M:%S')} Mosquitto runs on IP {mqtthost_ip} and port {mqttport} with SSL: {mqttuse_ssl}")
        
      client.on_connect = on_connect
      
      # subscribe to the defined topic!
      print(f"{dt.now().strftime('%Y-%m-%d %H:%M:%S')} Going to subscribe to topic: {mqtttopic}")
      client.subscribe(mqtttopic)
    
      while True:
        client.loop_start()
        
        while len(q)> 0:
          #if len(q)> 0: #This will implicitly convert q to a bool, which yields True if the deque contains any items and False if it is empty.
          data = q.popleft()  #get the first message which was received and delete
          if data[0] == "json":
            # set default values
            filesizeClip = filesizeSnapshot = filesizeThumbnail = 0
            filenameClip = filenameSnapshot = filenameThumbnail = " "
            urlClip = urlSnapshot = urlThumbnail = " "
            (filenameClip, filesizeClip,  urlClip, filenameSnapshot, filesizeSnapshot, urlSnapshot) = get_Frigate_obj(data[1], frigate_host_ip, frigate_http_port, object_storage_path)
            files=[]
            total_size = 0
            emailbody_text_to_be_send = emailbody_text
            if filesizeSnapshot > 0: # we have a snapshot  
                files.append(filenameSnapshot)
                total_size = total_size + filesizeSnapshot
                emailbody_text_to_be_send = emailbody_text_to_be_send + f"\n\nSnapshot url: {urlSnapshot}" 
            if filesizeClip > 0: # we have a clip  
                files.append(filenameClip)
                total_size = total_size + filesizeClip
                emailbody_text_to_be_send = emailbody_text_to_be_send + f"\n\nClip url: {urlClip}\n" 
                
            if 0 < total_size < email_maximum_size: #  total size of attachment files is smaller than kpnmail maximum which is 52428800 bytes              
                ret_code = send_mail(send_from=emailFrom, send_to=[emailTo], subject=emailtitel, 
                    message=emailbody_text_to_be_send, files=files,server=emailserver, port=emailport, 
                    username=emailusername, password=emailpassword, use_tls=emailuse_tls, 
                    object_storage_path=object_storage_path)                 
                if ret_code == 'ok':
                  print(f"{dt.now().strftime('%Y-%m-%d %H:%M:%S')} Mail has been send to {emailTo} with attachments:", *files, sep=" ")
            else:
                files = []
                emailbody_text_to_be_send = emailbody_text
                total_size = 0
                if 0 < filesizeSnapshot < email_maximum_size:  # just in case an extra check to avoid mail size overflow, will probably not happen as thumbnails are small
                  files.append(filenameSnapshot)
                  emailbody_text_to_be_send = emailbody_text_to_be_send + f"\n\nSnapshot url: {urlSnapshot}" 
                if total_size > 0:  
                  emailbody_text_to_be_send = emailbody_text_to_be_send + f"\n\nClip is not included. It is too large to be mailed.\n\nClip url: {urlClip}"
                  ret_code = send_mail(send_from=emailFrom, send_to=[emailTo], subject=emailtitel, 
                    message=emailbody_text_to_be_send, files=files, server=emailserver, 
                    port=emailport, username=emailusername, password=emailpassword, use_tls=emailuse_tls, 
                    object_storage_path=object_storage_path) 
                  if ret_code == 'ok':
                    print(f"{dt.now().strftime('%Y-%m-%d %H:%M:%S')} Mail has been send to {emailTo} with attachments:", *files, sep=" ")
          else: # if data[0] == 'no json'
            try:
              print(f"{dt.now().strftime('%Y-%m-%d %H:%M:%S')} Message => {data[1].decode()}")
            except:
              print(f"{dt.now().strftime('%Y-%m-%d %H:%M:%S')} Message => {data[1][0:45]} ... (truncated {type(data[1])})")

          print(f"{dt.now().strftime('%Y-%m-%d %H:%M:%S')} Messages in deque: {len(q)}")      
        client.loop_stop()


def run():
  # contact MQTT to get the topic messages and parse them, get thumnail from frigate and mail it
  processFrigateEventMessages(mqttclient_id=mqttclient_id, mqtttopic=mqtttopic, 
  mqttusername=mqttusername, mqttpassword=mqttpassword, mqtthost_ip=mqtthost_ip, 
      mqttport=mqttport, mqttsslport=mqttsslport, mqttuse_ssl=mqttuse_ssl, 
      mqttca_cert=mqttca_cert, emailFrom=emailFrom, emailTo=emailTo, 
      emailtitel=emailtitel, emailbody_text=emailbody_text, emailserver=emailserver, 
      emailport=emailport, emailusername=emailusername, emailpassword=emailpassword, 
      emailuse_tls=emailuse_tls, email_maximum_size=email_maximum_size, object_storage_path=object_storage_path)
  
if __name__ == '__main__':
    run()
