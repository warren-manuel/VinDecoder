from bs4 import BeautifulSoup
from collections import defaultdict
import requests


def get_vins_from_auction():
    AUCTION_URL = "https://www.houstontx.gov/police/auto_dealers_detail/Vehicles_Scheduled_For_Auction.htm"
    response = requests.get(AUCTION_URL)
    soup = BeautifulSoup(response.text, 'html.parser')
    vin_location_map = defaultdict(list)

    # Find all tables and search for VINs (17-character strings)
    for table in soup.find_all('table'):
        header_row = table.find_all('tr')[1]
        headers = [th.get_text(strip=True) for th in header_row.find_all('td')]
        if not headers:
            continue

        try:
            vin_idx = headers.index("VIN")
            addr_idx = headers.index("Storage Lot Address")
        except ValueError:
            continue  # required headers not found

        for row in table.find_all('tr')[2:]:  # skip header rows
            cells = row.find_all('td')
            if len(cells) <= max(vin_idx, addr_idx):
                continue

            vin = cells[vin_idx].get_text(strip=True).upper()
            address = cells[addr_idx].get_text(strip=True)

            vin_location_map[address].append(vin)

    return vin_location_map