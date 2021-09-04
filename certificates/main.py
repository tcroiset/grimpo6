import re
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Optional, List

import requests as requests

# Mandatory parameters
CLIENT_ID = ""  # API clientId
CLIENT_SECRET = ""  # API clientSecret
TM5_COOKIE = ""  # tm5-HelloAsso cookie


# Optional parameter
MIN_REGISTRATION_DATE: Optional[datetime] = None  # to filter on registrations date


class Registrations:
    def __init__(self):
        assert CLIENT_ID and CLIENT_SECRET and TM5_COOKIE, "Missing credentials"
        self.access_token = self.get_access_token()

    @staticmethod
    def get_access_token() -> str:
        data = {
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "grant_type": "client_credentials",
        }
        res = requests.post("https://api.helloasso.com/oauth2/token", data)
        content = res.json()
        return content["access_token"]

    def get(self, path: str, params: Optional[dict] = None) -> dict:
        res = requests.get(
            f"https://api.helloasso.com/v5/{path}",
            params,
            headers={"Authorization": f"Bearer {self.access_token}"},
        )
        return res.json()

    def list_forms(self) -> dict:
        return self.get("organizations/grimpo6/forms")

    def get_form_submissions(self, form_slug: str) -> List[int]:
        page_index = 1
        last_page_processed = False
        submissions = []
        print(f"Process Form {form_slug}")
        num_users = 0
        while not last_page_processed:
            print(f"Process page {page_index} of submissions")
            res = self.get(
                f"organizations/grimpo6/forms/Membership/{form_slug}/orders",
                {"pageSize": 100, "pageIndex": page_index},
            )
            for submission in res["data"]:
                ISO_8601_MS = r"%Y-%m-%dT%H:%M:%S.%f%z"
                date = submission["date"]
                date = re.sub(r"[0-9]\+([0-9]{2}):", "+\\1", date)
                registration_date = datetime.strptime(date, ISO_8601_MS)
                if MIN_REGISTRATION_DATE and registration_date < MIN_REGISTRATION_DATE:
                    continue
                submissions.append(submission["id"])
                num_users += len([x for x in submission["items"] if "user" in x])
            if res["pagination"]["pageIndex"] < res["pagination"]["totalPages"]:
                page_index += 1
            else:
                last_page_processed = True
        print(num_users, "submissions found")
        return submissions

    def get_safe_text(self, text: str) -> str:
        # Remove accent
        safe_text = (
            unicodedata.normalize("NFD", text).encode("ascii", "ignore").decode("utf-8")
        )
        # Remove special characters
        safe_text = re.sub(r"[^a-zA-Z0-9]+", " ", safe_text)
        # Remove extra spaces
        safe_text = re.sub(r" +", "-", safe_text.strip())
        # Lower case
        safe_text = safe_text.lower()
        return safe_text

    def save_file(self, form_slug: str, url: str, name: str):
        cookies = {"tm5-HelloAsso": TM5_COOKIE}
        r = requests.get(url, cookies=cookies)
        extension = url.split(".")[-1]
        path = f"{form_slug}/{name}.{extension}"
        with open(path, "wb") as f:
            f.write(r.content)

    def get_certificates(self, form_slug: str, submission_ids: List[int]):
        Path(form_slug).mkdir(exist_ok=True)
        for submission_id in submission_ids:
            res = self.get(f"orders/{submission_id}")
            for item in (x for x in res["items"] if "user" in x):
                first_name = item["user"]["firstName"]
                last_name = item["user"]["lastName"]
                prefix = f"{self.get_safe_text(last_name).capitalize()}_{self.get_safe_text(first_name).capitalize()}"
                certificate_field = next(
                    (
                        f
                        for f in item["customFields"]
                        if "certificat-medical" in self.get_safe_text(f["name"])
                    ),
                    None,
                )
                if certificate_field:
                    certificate_url = certificate_field["answer"]
                    self.save_file(form_slug, certificate_url, f"{prefix}-certificat")
                waiver_answer = next(
                    (
                        f
                        for f in item["customFields"]
                        if "decharge" in self.get_safe_text(f["name"])
                        or "attestation" in self.get_safe_text(f["name"])
                    ),
                    None,
                )
                if waiver_answer:
                    waiver_url = waiver_answer["answer"]
                    self.save_file(form_slug, waiver_url, f"{prefix}-attestation")


def get_form_slug(forms_data: List) -> str:
    num_of_forms = len(forms_data)
    for i, form in enumerate(forms_data, start=1):
        print(f"{i}: {form['title']}")
    print()
    while True:
        try:
            form_number = int(input(f"Select the form number: [1-{num_of_forms}]: "))
            if form_number not in range(1, num_of_forms + 1):
                raise ValueError
            return forms_data[form_number - 1]["formSlug"]
        except ValueError:
            print(f"Invalid input. Please enter a number between 1 and {num_of_forms}")


def select_and_process_form():
    registrations = Registrations()
    forms = registrations.list_forms()
    form_slug = get_form_slug(forms["data"])
    submission_ids = registrations.get_form_submissions(form_slug)
    registrations.get_certificates(form_slug, submission_ids)
    print("Files downloaded!")


if __name__ == "__main__":
    select_and_process_form()
