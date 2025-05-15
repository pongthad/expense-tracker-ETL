import os.path
import base64
import re
from datetime import datetime
from zoneinfo import ZoneInfo
from variables import *
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly","https://www.googleapis.com/auth/gmail.modify"]

class Service:
    today = datetime.now(ZoneInfo("Asia/Bangkok")).strftime('%Y/%m/%d')
    def __init__(self):
        creds = None
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists("token.json"):
            creds = Credentials.from_authorized_user_file("token.json", SCOPES)
            # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    "credentials.json", SCOPES
                )
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open("token.json", "w") as token:
                token.write(creds.to_json())
        try:
            # Call the Gmail API
            self.__service = build("gmail", "v1", credentials=creds)

        except HttpError as error:
            print(f"An error occurred: {error}")

    def get_emails(self):
        result = self.__service.users().messages().list(userId="me",labelIds=[labelIds],q=f"after:{self.today}").execute()
        self.__messages = result.get("messages",[])
    
    def extract_email_body(self):
        transact_date = []
        trans_no = []
        amount = []
        fees = []
        df = {}
        for msg in self.__messages[:5]: 
            msg_detail = self.__service.users().messages().get(userId='me', id=msg['id']).execute()
            mail_body = msg_detail.get('payload','').get('body','').get('data','')
            decoded_bytes = base64.urlsafe_b64decode(mail_body)
            mail_body = decoded_bytes.decode('utf-8')
            transact_date.append(self.__extract_data(trans_date_search_pattern,mail_body))
            trans_no.append(self.__extract_data(trans_no_search_pattern,mail_body))
            amount.append(self.__extract_data(amount_search_pattern,mail_body))
            fees.append(self.__extract_data(fee_search_pattern,mail_body))
        
        df = {
                        trans_date_txt : transact_date,
                        trans_no_txt : trans_no,
                        amount_txt : amount,
                        fee_txt : fees
                    }
        print(df)
        return df
    
    def __extract_data(self,search_pattern,text):
        match = re.search(search_pattern, text)
        if match:
            value = match.group(1)
            return value
        else:
            return 'null'

if __name__ == "__main__":
    service = Service()
    service.get_emails()
    emails = service.extract_email_body()
    