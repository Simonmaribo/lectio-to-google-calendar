from lectio import sdk
from dotenv import load_dotenv
from os import getenv
import datetime
import sys

from calendar_setup import get_calendar_service
from google_calendar import create_school_event, delete_school_events

sys.argv.append("--noauth_local_webserver")

load_dotenv()

subjects = {
    "EC": "Erhvervscase",
    "DA": "Dansk",
    "EN": "Engelsk",
    "TY": "Tysk",
    "EC-AF": "Afsætning (Erhvervscase)",
    "EC-VØ": "Virksomhedsøkonomi (Ehvervscase)",
    "AF": "Afsætning",
    "VØ": "Virksomhedsøkonomi",
    "IØ": "International Økonomi",
    "HI": "Historie",
    "ER": "Erhvervsjura",
    "MA": "Matematik"
}

def get_subject(hold):
    subject = hold.split(" ")

    if len(subject) > 1:
        return subjects[subject[1].upper()] if subject[1].upper() in subjects else "Ikke angivet"
    return "Ikke angivet"


def get_modul(obj):
    modul = {}
    hold = obj["hold"].split(", ")
    modul["subject"] = obj["navn"] if len(hold) > 1 else get_subject(hold[0])
    modul["location"] = None if obj["lokale"] == "None" else obj["lokale"]
    modul["description"] = None if obj["andet"] is None else "Ikke lavet endnu"

    time = obj["tidspunkt"].split(" ")
    year = int(time[0][-4:])
    date = time[0][:-5]  # "-YEAR"

    day = int(date.split("/")[0])
    month = int(date.split("/")[1])

    start = time[1]
    end = time[3]

    modul["start"] = datetime.datetime(year, month, day, int(start.split(":")[0]), int(start.split(":")[1])).isoformat()
    modul["end"] = datetime.datetime(year, month, day, int(end.split(":")[0]), int(end.split(":")[1])).isoformat()

    return modul



def get_moduler():
    date = datetime.date.today()
    iso_calendar = date.isocalendar()
    weeks_and_years = [
        (iso_calendar[0], iso_calendar[1]),
        (iso_calendar[0], iso_calendar[1] + 1) if iso_calendar[1] < 52 else (iso_calendar[0] + 1, 1)
    ]

    client = sdk(
        brugernavn=getenv('LECTIO_USERNAME'),
        adgangskode=getenv('LECTIO_PASSWORD'),
        skoleId=getenv('LECTIO_SCHOOLID')
    )

    moduler = []
    for week_and_year in weeks_and_years:
        result = client.skema(retry=True, uge=week_and_year[1], år=week_and_year[0])
        if "moduler" not in result:
            continue
        print(result["moduler"])
        for modul in result["moduler"]:
            if modul["status"] == "aflyst":  # "ændret, normal, aflyst"
                continue
            new_modul = get_modul(modul)
            if new_modul is not None:
                moduler.append(get_modul(modul))

    print(f"Loaded {len(moduler)} moduler")

    service = get_calendar_service()
    delete_school_events(service)
    for modul in moduler:
        create_school_event(
            service,
            subject=modul["subject"],
            location=modul["location"],
            start=modul["start"],
            end=modul["end"],
            description=modul["description"]
        )


get_moduler()
