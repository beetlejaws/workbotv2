import aiohttp
from google.oauth2.service_account import Credentials
from google.auth.transport.requests import Request


class GoogleService:
    def __init__(self, credentials_path: str, scopes: list[str]) -> None:
        self.creds = Credentials.from_service_account_file(
            credentials_path, scopes=scopes
        )
        self.creds.refresh(Request())
        self.access_token = self.creds.token


class GoogleSheets(GoogleService):
    def __init__(self, credentials_path: str):
        scopes = ['https://www.googleapis.com/auth/spreadsheets']
        super().__init__(credentials_path, scopes)
        

    async def get_sheet_data(self, sheet_id: str) -> list:
        url = f'https://sheets.googleapis.com/v4/spreadsheets/{sheet_id}/values/Sheet1!A:Z'
        headers = {'Authorization': f'Bearer {self.access_token}'}

        if not self.creds.valid:
            self.creds.refresh(Request())
            self.access_token = self.creds.token

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                data = await response.json()
                return data['values'][1:]
            

class GoogleDrive(GoogleService):
    def __init__(self, credentials_path: str):
        scopes = ['https://www.googleapis.com/auth/drive']
        super().__init__(credentials_path, scopes)
        self.url = 'https://www.googleapis.com/drive/v3/files'

    @staticmethod
    async def get_file_link(file_id: str) -> str:
        return f"https://drive.google.com/file/d/{file_id}/view"

    async def get_file_id_by_name(self, file_name: str, folder_id: str) -> str | None:
        query = f'"{folder_id}" in parents and name = "{file_name}"'
        params = {
            'q': query,
            'fields': 'files(id, name)'
        }
        headers = {'Authorization': f'Bearer {self.access_token}'}

        if not self.creds.valid:
            self.creds.refresh(Request())
            self.access_token = self.creds.token

        async with aiohttp.ClientSession() as session:
            async with session.get(self.url, headers=headers, params=params) as response:
                data = await response.json()

                if not data.get('files'):
                    return None
                
                return data['files'][0]['id']