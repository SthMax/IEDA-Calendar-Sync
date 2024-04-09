# IEDA-Calendar-Sync
Sync HKUST IEDA Events Calendar to Google Calendar

## Usage

Create a settings.json based on settings-template.json. (Set last_eventID to more current events to avoid performance issue on first run)

Create a google service account and let it manage the designated calendar.

Retreive service.json from google service account https://cloud.google.com/iam/docs/keys-create-delete#iam-service-account-keys-create-console and place it into the git folder.

Then run main.py, all logs are dumped in scrapping.log.

## Tips: 
Use crontab to run this script in schedule

