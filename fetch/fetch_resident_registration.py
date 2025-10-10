import requests
from interfaces.resident_registration_output import ResidentRegistrationOutput
from config import KIOSK_APP_URL

def fetch_resident_registration(resident_registration_output: ResidentRegistrationOutput):
    response = requests.post(
        url=f"{KIOSK_APP_URL}/resident-registration",
        json={
            "registrationNumber": resident_registration_output.registration_number,
            "type": resident_registration_output.type,
            "copyNumber": resident_registration_output.number
        }
    )

    return response.status_code