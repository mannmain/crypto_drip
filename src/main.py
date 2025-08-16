import time
from datetime import datetime
from random import randint, shuffle

from config import TG_NAME_PARSE
from tg.notification import send_msg
from view.client import Client
from view.ws import WS
from loguru import logger
import pandas as pd


def main():
    while True:
        start_time = time.time()
        creds_df = pd.read_excel('creds/creds.xlsx', sheet_name='Лист1', dtype=str)
        creds_df = creds_df.fillna('')
        result = creds_df.to_dict(orient='records')
        result = [i for i in result if str(i['status']) == '1']
        shuffle(result)
        for data in result:
            count_error = 0
            while True:
                try:
                    client = Client(**data)
                    drip_ws = WS(client)
                    # logger.debug(drip_ws)
                    drip_ws.start()
                    drip_ws.logout()

                    client.ws.close()
                    time.sleep(randint(20, 90))
                    break
                except Exception as ex:
                    count_error += 1
                    logger.error(f'[{data["num"]}] | Error Global: {ex}')
                    if ('bad proxy' in str(ex)) or count_error > 10:
                        msg = f'{TG_NAME_PARSE}\n{datetime.now().strftime("%m.%d %H:%M")}\n[ОШИБКА]\n{data["num"]}\nex: {ex}'
                        send_msg(msg)
                        break
                    pass
        while True:
            if (time.time() - start_time) > (6*3600 + 120):
                break
            time.sleep(60)


if __name__ == '__main__':
    main()
