import time
from random import randint

from view.client import Client
from view.ws import WS
from loguru import logger
import pandas as pd


def main():
    while True:
        creds_df = pd.read_excel('creds/creds.xlsx', sheet_name='Лист1')
        result = creds_df.to_dict(orient='records')
        for data in result:
            try:
                client = Client(**data)
                drip_ws = WS(client)
                logger.debug(drip_ws)
                drip_ws.start()
                drip_ws.logout()

                client.ws.close()
                time.sleep(randint(60, 300))
            except Exception as ex:
                logger.error(f'[{data["num"]}] | Error Global: {ex}')
                pass
        time.sleep(randint(6*3600 + 120, 6*3600 + 300))


if __name__ == '__main__':
    main()
