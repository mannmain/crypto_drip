import time

import requests

from config import TG_GROUP_ID, TG_API_TOKEN


def send_file(path):
    params = {
        'chat_id': TG_GROUP_ID,
        'disable_notification': False,
    }
    files = {
        'document': open(f'{path}', 'rb'),
    }
    while True:
        try:
            response = requests.post(f'https://api.telegram.org/bot{TG_API_TOKEN}/sendDocument', files=files, params=params)
            if response.status_code == 200:
                break
            else:
                try:
                    print(f'ERROR SEND MSG status {response.status_code}) - {response.text}')
                except:
                    print(f'ERROR SEND MSG status {response.status_code})')
        except Exception as ex:
            print(f"ERROR SEND MSG - {ex}")


def send_msg(msg, parser_analysis=False):
    group_id = TG_GROUP_ID
    api_token = TG_API_TOKEN
    json_data = {
        'chat_id': group_id,
        'text': msg,
        'disable_notification': False,
    }
    while True:
        try:
            response = requests.post(f'https://api.telegram.org/bot{api_token}/sendMessage', json=json_data)
            if response.status_code == 200:
                break
            else:
                try:
                    print(f'ERROR SEND MSG status {response.status_code}) - {response.text}')
                except:
                    print(f'ERROR SEND MSG status {response.status_code})')
        except Exception as ex:
            print(f"ERROR SEND MSG - {ex}")
            time.sleep(10)