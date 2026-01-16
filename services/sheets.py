import pandas as pd
import io
import requests

class SheetsService:
    def __init__(self):
        pass

    def get_prompts_from_sheet(self, sheet_url: str):
        """
        Reads a Public Google Sheet URL and returns a list of prompts.
        Assumes the first column contains the prompts.
        """
        try:
            # Convert normal URL to Export CSV URL
            # https://docs.google.com/spreadsheets/d/ID/edit?usp=sharing -> https://docs.google.com/spreadsheets/d/ID/export?format=csv
            
            if "docs.google.com/spreadsheets" not in sheet_url:
                print("Invalid Google Sheets URL")
                return []

            # Extract ID
            # This is a naive extraction, but covers most copy-paste cases
            try:
                sheet_id = sheet_url.split("/d/")[1].split("/")[0]
            except:
                print("Could not extract Sheet ID")
                return []
                
            csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
            
            print(f"Fetching CSV from: {csv_url}")
            response = requests.get(csv_url)
            response.raise_for_status()
            
            df = pd.read_csv(io.StringIO(response.text))
            
            # Assume first column has the prompts
            # Filter out empty rows
            prompts = df.iloc[:, 0].dropna().astype(str).tolist()
            
            return prompts

        except Exception as e:
            print(f"Error reading sheet: {e}")
            return []
