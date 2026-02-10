import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

SCOPE = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

def connect_sheets():
    creds = ServiceAccountCredentials.from_json_keyfile_name(
        "credentials.json", SCOPE
    )
    client = gspread.authorize(creds)
    return client


def get_class_data(client, spreadsheet_name, class_name):
    sheet = client.open(spreadsheet_name).worksheet(class_name)
    data = sheet.get_all_records()
    return pd.DataFrame(data), sheet


def add_attendance_column(sheet, date):
    headers = sheet.row_values(1)
    if date not in headers:
        sheet.add_cols(1)
        sheet.update_cell(1, len(headers) + 1, date)
