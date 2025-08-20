from io import BytesIO
import json
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

    def check_creds(self):
        if not self.creds.valid:
            self.creds.refresh(Request())
            self.access_token = self.creds.token


class GoogleSheets(GoogleService):
    def __init__(self, credentials_path: str):
        scopes = ['https://www.googleapis.com/auth/spreadsheets']
        super().__init__(credentials_path, scopes)
        

    async def get_sheet_data(self, sheet_id: str) -> list:
        url = f'https://sheets.googleapis.com/v4/spreadsheets/{sheet_id}/values/Sheet1!A:Z'
        headers = {'Authorization': f'Bearer {self.access_token}'}

        self.check_creds()

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
    def get_folder_link(folder_id: str) -> str:
        return f'https://drive.google.com/drive/folders/{folder_id}'
    
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

        self.check_creds()

        async with aiohttp.ClientSession() as session:
            async with session.get(self.url, headers=headers, params=params) as response:
                data = await response.json()

                if not data.get('files'):
                    return None
                
                return data['files'][0]['id']
            
    async def upload_file(self, file_name: str, file_data: BytesIO, folder_id: str):

        self.check_creds()

        upload_url = 'https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart'

        metadata = {
            'name': file_name,
            'parents': [folder_id]
        }

        writer = aiohttp.MultipartWriter('related')

        metadata_part = writer.append(
            json.dumps(metadata),
            {'Content-Type': 'application/json; charset=UTF-8'}
        )

        file_bytes = file_data.getvalue()
        file_part = writer.append(
            file_bytes,
            {'Content-Type': 'application/octet-stream'},
        )

        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': f'multipart/related; boundary={writer.boundary}'
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(upload_url, headers=headers, data=writer) as response:
                data =  await response.json()
                return data['id']
            
    async def get_files_by_name(self, file_name: str, folder_id: str):

        self.check_creds()

        query = f"'{folder_id}' in parents and name contains '{file_name}'"
        params = {
            'q': query,
            'fields': 'files(id, name, createdTime)',
            'orderBy': 'createdTime desc'
        }
        headers = {'Authorization': f'Bearer {self.access_token}'}

        async with aiohttp.ClientSession() as session:
            async with session.get(self.url, headers=headers, params=params) as response:
                data = await response.json()
                files = data.get('files', [])
                return files
            
    async def get_latest_version_date(self, file_name: str, folder_id: str):
        versions = await self.get_files_by_name(file_name, folder_id)
        if not versions:
            return None
        
        return versions[0]['createdTime']