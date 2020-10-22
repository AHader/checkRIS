#!/usr/bin/env python3
import smtplib
import os.path
import requests
import json
import re
import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

SETTINGS = 'ris.covid'
HEADERS = {
    'Content-type': 'application/json',
}

slack_token = 'xoxb-000000000000-1111111111111-EqpxdPJ9S25rfNCvke6vDbjh'
slack_channelA = 'RPkKH4uzQ'
slack_channelB =  'LCh2WSk8k'

email_accountname = 'bot@acme.com'
email_accesstoken = 'DZH3Sd1xWS7euuPzVjqLnmM'
email_server = 'smtp.acme.com'
email_port = 587
email_targets = ["info@acme.com", "data@acme.com"]

def getRIS(id):
    url = "https://www.ris.bka.gv.at/Dokumente/BgblAuth/BGBLA_2020_II_%s/BGBLA_2020_II_%s.html" % (id, id)
    r = requests.get(url, allow_redirects=True)
    open('ris.tmp', 'wb').write(r.content)
    return open('ris.tmp', 'r').read(-1)

def isCovidLV(content):
    m = re.search('\\d+(?=\\..COVID-19-LV-Novelle)', content)
    return m

def isCovidMV(content):
    m = re.search('\\d+(?=\\..COVID-19-MV-Novelle)', content)
    return m

def exists(content):
    m = re.search('(?<=Das Dokument).+(?=ist im RIS-Datenbestand nicht enthalten)', content)
    return m == None

def checkIfSettingsExist():
    return os.path.exists(SETTINGS) and os.path.isfile(SETTINGS)

def sendEmail(content):
    s = smtplib.SMTP(host=email_server, port=587)
    s.starttls()
    s.login(email_accountname, email_accesstoken)
    for email in email_targets:
        msg = MIMEMultipart()
        msg['From']='bot@acme.com'
        msg['To']=email
        msg['Subject']="Neue COVID-19-LV-Novelle"
        msg.attach(MIMEText(content, 'plain'))
        s.send_message(msg)       
        del msg

def postSlack(channels, text, blocks):
    for channel in channels:
        requests.post('https://slack.com/api/chat.postMessage', {
            'token': slack_token,
            'channel': channel,
            'text': text,
            'blocks': json.dumps(blocks) if blocks else None
        }).json()

def createLinks(id, num, kind):
    return [{
			"type": "header",
			"text": {
				"type": "plain_text",
				"text": ":mega: Neue Covid-19-%s-Novelle wurde im RIS veröffentlicht" % (kind),
				"emoji": True
			}
		},
        {  
            "type": "section",
            "text": {  
                "type": "mrkdwn",
                "text": "Änderungen der <%s|*%s.* COVID-19-%s-Novelle>" % ("https://www.ris.bka.gv.at/Dokumente/BgblAuth/BGBLA_2020_II_%s/BGBLA_2020_II_%s.html" % (id, id), num, kind)
            }
        },
        {  
            "type": "section",
            "text": {  
               "type": "mrkdwn",
               "text": "Aktuell gültige, konsolidierte <https://www.ris.bka.gv.at/GeltendeFassung.wxe?Abfrage=Bundesnormen&Gesetzesnummer=20011162|Covid-19-%s>" % (kind)
            }
        },
        {
            "type": "section",
            "text": {
               "type": "mrkdwn",
               "text": "Aktuell gültiges, konsolidiertes <https://www.ris.bka.gv.at/GeltendeFassung.wxe?Abfrage=Bundesnormen&Gesetzesnummer=20011073|Covid-19-MG>"
            }
        }]

id = 445

if (checkIfSettingsExist()):
    id = int(open(SETTINGS).read(-1))
else:
    id = 445

while True:
    print ("%s checking %s" % (datetime.datetime.now().strftime("%d.%b %Y %H:%M:%S"), id))
    content = getRIS(id)
    if (not exists(content)):
        break
    m = isCovidLV(content)
    if (m):
        postSlack([slack_channelA, slack_channelB], "Neue Covid-19-LV-Novelle wurde im RIS veröffentlicht", createLinks(id, m.group(0), "LV"))
        sendEmail("%s. COVID-19-LV-Novelle: %s" % (m.group(0), "https://www.ris.bka.gv.at/Dokumente/BgblAuth/BGBLA_2020_II_%s/BGBLA_2020_II_%s.html" % (id, id)))
    m = isCovidMV(content)
    if (m):
        postSlack([slack_channelA, slack_channelB], "Neue Covid-19-MV-Novelle wurde im RIS veröffentlicht", createLinks(id, m.group(0), "MV"))
        sendEmail("%s. COVID-19-MV-Novelle: %s" % (m.group(0), "https://www.ris.bka.gv.at/Dokumente/BgblAuth/BGBLA_2020_II_%s/BGBLA_2020_II_%s.html" % (id, id)))
    id = id + 1
open(SETTINGS, "w").write("%s" % (id))
