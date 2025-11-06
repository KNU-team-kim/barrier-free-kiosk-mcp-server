import requests
from interfaces.move_in_output import MoveInOutput
from config import KIOSK_APP_URL

def fetch_move_in(move_in_output: MoveInOutput):
    response = requests.post(
        url=f"{KIOSK_APP_URL}/move-in",
        json={
            "name": move_in_output.name,
            "phoneNumber": move_in_output.phone_number,
            "reason": move_in_output.reason,
            "newAddress": {
                "sido": move_in_output.after_sido,
                "sigungu": move_in_output.after_sigungu,
                "roadName": move_in_output.after_road_name,
                "mainBuildingNumber": int(move_in_output.after_building_number_main),
                "subBuildingNumber": int(move_in_output.after_building_number_sub) if move_in_output.after_building_number_sub is not None else None,
                "detail": move_in_output.after_detail_address
            }
        }
    )

    return response.status_code

def fetch_check_phone_number(phone_number: str, name: str):
    response = requests.get(
        url=f"{KIOSK_APP_URL}/move-in/check",
        params={"phoneNumber": phone_number, "name": name}
    )

    if response.status_code != 200: return None
    
    return response.json()

def fetch_retrieve_address(name: str, phone_number: str):
    response = requests.get(
        url=f"{KIOSK_APP_URL}/move-in/address",
        params={"name": name, "phoneNumber": phone_number}
    )

    if response.status_code != 200: return None
    
    return response.json()