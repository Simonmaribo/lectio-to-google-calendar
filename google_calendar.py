import datetime
import os

import googleapiclient.errors


def get_school_events(service, results: int = 50):
    # get datetime of the start of the week
    now = datetime.datetime.utcnow()
    start_of_week = now - datetime.timedelta(days=now.weekday()+1)

    print(f'Getting next {results} events')
    events_result = service.events().list(
        calendarId=os.getenv("GOOGLE_CALENDAR_ID"),
        timeMin=start_of_week.isoformat()+"Z",
        maxResults=results, singleEvents=True,
        orderBy='startTime').execute()
    events = events_result.get('items', [])

    if not events:
        print('No upcoming events found.')
        return []

    school_events = list(filter(lambda x: "summary" in x and x.get("summary").endswith("- Lectio"), events))
    return school_events


def delete_school_events(service):
    events = get_school_events(service)
    print(f"Deleting {len(events)} events")

    success = 0

    for event in events:
        try:
            service.events().delete(
                calendarId=os.getenv("GOOGLE_CALENDAR_ID"),
                eventId=event['id']
            ).execute()
            success += 1
        except googleapiclient.errors.HttpError:
            print("Failed to delete event: " + (event.get("summary") if "summary" in event else ""))

    print(f"Succesfully deleted {success} events")


def create_school_event(service, subject, location, start, end, description):
    try:
        event = service.events().insert(
            calendarId=os.getenv("GOOGLE_CALENDAR_ID"),
            body={
                "summary": f"{subject} - Lectio",
                "description": description if description is not None else "Automatisk genereret event fra Lectio",
                "location": f"{location} - Hillerød HHX" if location is not None else "Hillerød HHX",
                "start": {
                    "dateTime": start,
                    "timeZone": "Europe/Copenhagen"
                },
                "end": {
                    "dateTime": end,
                    "timeZone": "Europe/Copenhagen"
                }
            }
        ).execute()
    except googleapiclient.errors.HttpError:
        print("Failed to create event: %s %s %s %s", subject, location, start, end)