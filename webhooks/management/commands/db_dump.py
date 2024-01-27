import csv

from django.core.management.base import BaseCommand
from webhooks.models import Case
from datetime import datetime

def openAsDict(file_path):
    with open(file_path) as fo:
        # Merge first and second rows to use as dictionary keys
        data = list(csv.reader(fo))
        headers = ["state"]
        headers.extend(
            [f"{data[0][x]}-{data[1][x]}" for x in range(1, len(data[0]))]
        )
    with open(file_path) as fo:
        # Now read the data as a dictionary
        results = list(csv.DictReader(fo, fieldnames=headers))
        # Remove the first two rows and the last row
        results.pop(0)
        results.pop(0)
        results.pop()

    return results


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("file_path", type=str)

    def handle(self, *args, **options):
        file_path = options["file_path"]

        results = openAsDict(file_path)
        final_results = {} # Keep track of the dates we've already seen

        for r in results:
            state = r["state"]

            if not final_results.get(state):
                final_results[state] = {}

            for y in r:
                if y != "state":
                    z = y.split("-")

                    if not final_results.get(state).get(z[0]):
                        final_results[state][z[0]] = {}

                    numbers = 0
                    # Check if number is valid integer
                    try:
                        numbers = int(r[y])
                    except Exception as e:
                        print(f"Integer conversion failed for {state} {z[0]}: {e}")
                        continue

                    if "TCIN" in z[1]:
                        final_results[state][z[0]]["tcin"] = numbers
                    elif "TCFN" in z[1]:
                        final_results[state][z[0]]["tcfn"] = numbers
                    elif "Cured" in z[1]:
                        final_results[state][z[0]]["cured"] = numbers
                    elif "Death" in z[1]:
                        final_results[state][z[0]]["death"] = numbers
                    else:
                        pass

        # TEST
        # print(final_results.get("Punjab").get("25/03/20"))
        # print(len(final_results.get("Maharashtra").keys()))

        for m in final_results:
            # Create several case instances
            cases = []

            data = final_results.get(m)

            for d in data:
                case = data.get(d)
                # Convert date into the proper format
                try:
                    dateTimeObj = datetime.strptime(d, "%d/%m/%y")
                except:
                    print(f"date conversion for {d} failed")
                    continue

                cases.append(
                    Case(
                        state=m,
                        date=dateTimeObj,
                        death=case.get("death"),
                        tcin=case.get("tcin"),
                        tcfn=case.get("tcfn"),
                        cured=case.get("cured")
                    )
                )

            # Write cases to database
            Case.objects.bulk_create(cases)
