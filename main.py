import datetime
import json
import logging
import os.path
from bs4 import BeautifulSoup
import urllib.request

from google.auth.transport.requests import Request
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/calendar"]
HOMEPAGE = "http://ieda.ust.hk/eng/events.php?catid=6&sid=50"
SITE = "http://ieda.ust.hk/eng/event_detail.php?type=E&id="

def scrapping(service, settings):
  eventID = settings["eventID"]

  HOMEPAGE = "http://ieda.ust.hk/eng/events.php?catid=6&sid=50"

  contents = urllib.request.urlopen(HOMEPAGE).read()
  soup = BeautifulSoup(contents, 'html.parser')

  # Get the latest event ID
  lastEventID = int(soup.find('div', class_='info-block__date active').attrs['data-tab'])

  if eventID > lastEventID:
    logging.info("No new event")
    return None

  contents = urllib.request.urlopen(SITE+str(eventID)).read()
  soup = BeautifulSoup(contents, 'html.parser')

  title = soup.find(class_='context__subtitle').text.strip() #Joint OM/IE Seminar

  if title.find("Seminar") == -1:
    logging.info("Not a seminar")
    return scrapping(service, eventID+1)



def main():
  """Shows basic usage of the Google Calendar API.
  Prints the start and name of the next 10 events on the user's calendar.
  """
  creds = None
  settings = None

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

    # Call the Calendar API
    now = datetime.datetime.utcnow().isoformat() + "Z"  # 'Z' indicates UTC time
    print("Getting the upcoming 10 events")
    events_result = (
        service.events()
        .list(
            calendarId=settings["calendarId"],
            timeMin=now,
            maxResults=10,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )
    events = events_result.get("items", [])

    if not events:
      print("No upcoming events found.")
      return

    # Prints the start and name of the next 10 events
    for event in events:
      start = event["start"].get("dateTime", event["start"].get("date"))
      print(start, event["summary"])

  except HttpError as error:
    print(f"An error occurred: {error}")


if __name__ == "__main__":
  main()