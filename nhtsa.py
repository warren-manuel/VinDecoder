import requests


def decode_vin(vin):
    NHTSA_API = "https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVinValuesExtended/{vin}?format=json"
    url = NHTSA_API.format(vin=vin)
    response = requests.get(url)
    try:
        result = response.json()["Results"][0]
        return result
    except Exception as e:
        print(f"Failed to decode VIN {vin}: {e}")
        return None
    
def is_manual(decoded_info):
    transmission = decoded_info.get("TransmissionStyle", "") or decoded_info.get("TransmissionType", "")
    return "manual" in transmission.lower()