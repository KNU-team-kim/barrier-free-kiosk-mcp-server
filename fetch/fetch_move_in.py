import requests
from interfaces.move_in_output import MoveInOutput
from config import KIOSK_APP_URL

def fetch_move_in(move_in_output: MoveInOutput):
    new_address = move_in_output.after_address.split(",")

    response = requests.post(
        url=f"{KIOSK_APP_URL}/move-in",
        json={
            "name": move_in_output.name,
            "phoneNumber": move_in_output.phone_number,
            "reason": move_in_output.reason,
            "newAddress": {
                "sido": new_address[0],
                "sigungu": new_address[1],
                "roadName": new_address[2],
                "buildingNumber": int(new_address[3]),
                "detail": new_address[4]
            }
        }
    )

    return response.status_code