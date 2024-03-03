import datetime
import json
import logging
import os.path
from bs4 import BeautifulSoup
import urllib.request

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/calendar"]
HOMEPAGE = "http://ieda.ust.hk/eng/events.php?catid=6&sid=50"
SITE = "http://ieda.ust.hk/eng/event_detail.php?type=E&id="
DEFAULT_TIME_INTERVAL = 1.5
DEFAULT_ID_FORWAD = 3

def constructEventBody(event):
  startTime = datetime.datetime.strptime(event["Date"] + " " + event["Time"].replace(".", "").capitalize(), "%d %B %Y (%A) %I:%M %p")
  endTime = startTime + datetime.timedelta(hours=DEFAULT_TIME_INTERVAL)

  description = event["Title"] + "\n\nBy " + event["Speaker"]
  if "School" in event:
      description += "\nFrom " + event["School"]
  description += "\n\n" + event["Link"] + "\n\n" + event["Abstract"] + "\n\n" + event["Bio"]

  res = {
    "summary": (event['Type'] + " by " + event["Speaker"]),
    "location": event["Venue"],
    "description": description,
    "start": {
      "dateTime": startTime.isoformat(),
      "timeZone": "Asia/Hong_Kong",
    },
    "end": {
      "dateTime": endTime.isoformat(),
      "timeZone": "Asia/Hong_Kong",
    },
    # "recurrence": ["RRULE:FREQ=DAILY;COUNT=1"],
    "reminders": {
      "useDefault": False,
      "overrides": [
        {"method": "popup", "minutes": 15},
      ],
    },
  }
  return res

def adding(service, calendarID, event):
  try:
    event = service.events().insert(calendarId=calendarID, body=constructEventBody(event)).execute()
    logging.info("Event created: %s" % (event.get("htmlLink")))
  except Exception as error:
    logging.error(f"Error Occured when Adding: {error}")

def scrapping(eventID):
  contents = urllib.request.urlopen(SITE+str(eventID)).read()
  soup = BeautifulSoup(contents, 'html.parser')

  event = dict()

  eventType = soup.find(class_='context__subtitle') #Joint OM/IE Seminar / Seminar / Thesis Examination / etc

  if eventType is None:
    logging.info("Invalid event at " + str(eventID))
    return None
  else:
    event['Type'] = eventType.text.strip()

  event["Title"] = soup.find(class_='context__title').text.strip() #Title
  
  for label, value in zip(soup.find_all('span', class_='item-label'), soup.find_all('span', class_='item-value')):
    event[label.text] = value.text #Date, Time, Venue, Speaker, etc, School is Optional

  event["Abstract"] = soup.find(class_='context__text abstract').text.strip() #Abstract

  speaker_bio = soup.find(class_='context__text speaker')
  if speaker_bio is not None:
    event["Bio"] = speaker_bio.text.strip() #Bio
  else:
    logging.info("No Bio for event at " + str(eventID))
    event["Bio"] = ""

  event["Link"] = SITE+str(eventID) #Link

  return event



def main():
  creds = None
  settings = None

  logging.basicConfig(filename='scrapping.log', level=logging.INFO)

  logging.info("Run at " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

  if os.path.exists("settings.json"):
    with open("settings.json", "r") as f:
      settings = json.load(f)
  else:
    logging.error("settings.json not found")
    return None

  if os.path.exists("service.json"):
    creds = service_account.Credentials.from_service_account_file(
      "service.json", scopes=SCOPES
    )
  else:
    logging.error("service.json not found")
    return None
  
  try:
    service = build("calendar", "v3", credentials=creds)
  except HttpError as error:
    logging.error(f"Build Service Failed: {error}")
    return None

  try:
    contents = urllib.request.urlopen(HOMEPAGE).read()
  except Exception as error:
    logging.error(f"Urllib error occurred: {error}")
    return None
  
  soup = BeautifulSoup(contents, 'html.parser')
  lastEventID = int(soup.find('div', class_='info-block__date active').attrs['data-tab'])
  first_event = settings['last_eventID'] + 1

  if first_event > lastEventID:
    logging.info("No new event")
    return None

  for i in range(first_event, lastEventID + DEFAULT_ID_FORWAD):
  # Get the latest event ID
    try:
      event = scrapping(i)
    except Exception as error:
      logging.error(f"Error Occured when Scrapping: {error}")
      logging.error(f"Event ID: {i}")
      return
    
    if event is not None:
      settings['last_eventID'] = i
      adding(service, settings["calendarId"], event)
  
  with open("settings.json", "w") as f:
    json.dump(settings, f)


if __name__ == "__main__":
  main()