import json
from random import randint

import requests
from loguru import logger
from solana.rpc.commitment import Commitment
from solders.transaction import VersionedTransaction

from config import LOG_MORE
from view.helper import *


class WS:
    def __init__(self, client):
        super().__init__()
        self.client = client

    def start(self):
        if not self.login():
            logger.error(f'[{self.client.num}] | {self.client.address} | Error in login')
        # self.first_login()
        # self.buy_droplets(1000)
        # self.get_rank_in_last_month()
        # self.check_collection_on_acc('Pudgy')
        # self.check_unlock_price()


        self.get_sponsoreds()
        self.up_lvl_to_bronze()
        if self.check_stop_need_rank():
            return

        if self.check_available_claim_droplets():
            self.claim_droplets()
        if self.check_available_rarity_lockin():
            self.rarity_lockin()
        self.sub_list_channels()
        if self.check_xp_status(11_000):
            self.add_butch_likes()
        data = self.secure_all_my_collections()
        if data['status'] == 'empty':
            self.secure_all_my_collections(rarity='rare')
            if data['status'] == 'empty':
                self.secure_all_my_collections(rarity='common')
        self.get_droplet_balance()

    def check_unlock_price(self):
        message = self.send_and_receive('unlock_purchase_option', {})
        purchase_option = message[4]['response']['result']['purchase_option']
        if purchase_option:
            message_session = self.get_session_data()
            username = message_session[4]['username']
            message_monthly_recap = self.send_and_receive("monthly_recap", {'username': username})
            last_rank = message_monthly_recap[4]['response']['result']['badge']['current_name']
            current_xp = message_monthly_recap[4]['response']['result']['badge']['current_xp']
            logger.info(f'[{self.client.num}] | {self.client.address} | {self.client.count_msg} | rank: {last_rank} | xp: {current_xp} | {purchase_option["price_display"]} ({purchase_option["name"]})')
            # logger.info(f'[{self.client.num}] | {self.client.address} | {self.client.count_msg} | {purchase_option["price_display"]} ({purchase_option["name"]})')
        # if message[4]['response']['ok']:

    def get_sponsoreds(self):
        message = self.send_and_receive("get_sponsoreds", {})
        if message[4]['response']['ok']:
            results = [i for i in message[4]['response']['results'] if not i['claimed']]
            if len(results) == 0:
                if LOG_MORE:
                    logger.success(f'[{self.client.num}] | {self.client.address} | {self.client.count_msg} | [Sponsoreds] None')
                return
            drop_key_list = [i['drop_key'] for i in results]
            for drop_key in drop_key_list:
                status = self.claim_sponsored(drop_key)
                if not status:
                    logger.error(f'[{self.client.num}] | {self.client.address} | {self.client.count_msg} | [Sponsoreds] Error')
                    return

    def claim_sponsored(self, drop_key: str):
        message = self.send_and_receive("claim_sponsored", {'drop_key': drop_key})
        if message[4]['status'] == 'ok':
            if message[4]['response']['ok']:
                logger.success(f'[{self.client.num}] | {self.client.address} | {self.client.count_msg} | [Claim Sponsored] drop_key: {drop_key}')
                return True
        return False

    def buy_droplets(self, count_droplets: int):
        while True:
            try:
                if (self.check_xp_status() > 0) or (self.get_droplet_balance() > 0):
                    # if self.get_droplet_balance() > 960:
                    #     print('NICEHRITWEOHIUHIOWE')
                    return
                data = {'slug': f"{count_droplets}-droplets", 'return_url': "https://drip.haus/my-collectibles"}
                message = self.send_and_receive("get_droplet_payment_link", data)
                url = message[4]['response']['result']['url']  # https://spherepay.co/pay/paymentLink_cdfb511aa7c549868241a37af9cc7f10
                end_url = url.split('/')[-1]  # paymentLink_cdfb511aa7c549868241a37af9cc7f10
                headers = {
                    'accept': 'application/json, text/plain, */*',
                    'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7,zh-CN;q=0.6,zh;q=0.5',
                    'content-type': 'application/json',
                    'origin': 'https://spherepay.co',
                    'priority': 'u=1, i',
                    'referer': 'https://spherepay.co/',
                    'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-platform': '"Windows"',
                    'sec-fetch-dest': 'empty',
                    'sec-fetch-mode': 'cors',
                    'sec-fetch-site': 'same-site',
                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
                }

                response = requests.get(
                    f'https://api.spherepay.co/v1/public/paymentLink/{end_url}',
                    headers=headers,
                )
                line_item_id = response.json()['data']['paymentLink']['lineItems'][0]['id']
                # print(f'{line_item_id=}')
                nanoid = self.client.get_nano_id()
                # print(f'{nanoid=}')
                params = {
                    'inputMint': 'So11111111111111111111111111111111111111112',
                    'state': 'AL',
                    'lineItems': '[{"id":"' + str(line_item_id) + '","quantity":1}]',
                    'paymentReference': nanoid,
                    'network': 'sol',
                    'customFields': '[]',
                    'skipPreflight': 'false',
                }

                json_data = {
                    'account': self.client.address,
                    'skipPreflight': False,
                }

                response = requests.post(
                    f'https://api.spherepay.co/v1/public/paymentLink/pay/{end_url}',
                    params=params,
                    headers=headers,
                    json=json_data,
                )
                txn_base64 = response.json()['transaction']
                # print(f'{txn_base64=}')
                from solana.rpc.api import Client
                from solana.rpc.types import TxOpts
                from solana.rpc.commitment import Confirmed
                from solana.transaction import Keypair
                from solders.message import to_bytes_versioned
                import base64
                SOLANA_RPC_URL = "https://api.mainnet-beta.solana.com"

                client = Client(SOLANA_RPC_URL, commitment=Commitment("confirmed"), timeout=30)

                keypair = Keypair.from_base58_string(self.client.pk)

                txn_data = base64.b64decode(txn_base64)
                raw_tx = VersionedTransaction.from_bytes(txn_data)
                signature = keypair.sign_message(to_bytes_versioned(raw_tx.message))
                signed_txn = VersionedTransaction.populate(raw_tx.message, [signature, raw_tx.signatures[1]])

                opts = TxOpts(skip_preflight=False, preflight_commitment=Confirmed, skip_confirmation=False)
                result = client.send_transaction(signed_txn, opts=opts)
                tx_signature = result.value
                solscan_url = f"https://solscan.io/tx/{tx_signature}"
                logger.success(f'[{self.client.num}] | {self.client.address} | {self.client.count_msg} | [Buy Droplets] {solscan_url}')
                while True:
                    time.sleep(15)
                    if self.get_droplet_balance() >= 1000:
                        return
                    else:
                        logger.warning(f'[{self.client.num}] | {self.client.address} | {self.client.count_msg} | [Waiting Droplets] {solscan_url}')
            except Exception as ex:
                logger.error(f'[{self.client.num}] | {self.client.address} | {self.client.count_msg} | [Error] {ex}')
                if 'EOF occurred in violation of protocol (_ssl.c' in str(ex):
                    raise ex
                time.sleep(15)

    def check_collection_on_acc(self, name_col: str):
        data = {
            "pubkey": self.client.address,
            "limit": 12,
            "offset": 0,
            "rarity": "",
            "type": "",
            "search": f"{name_col}",
            "is_hidden": False
        }
        message = self.send_and_receive("get_vault", data)
        if message[4]['response']['ok']:
            results = message[4]['response']['results']
            if len(results) != 0:
                logger.success(
                    f'[{self.client.num}] | {self.client.address} | {self.client.count_msg} | [Check col] {name_col=} on account')
                return True
            else:
                logger.warning(
                    f'[{self.client.num}] | {self.client.address} | {self.client.count_msg} | [Check col] {name_col=} NOT on account')
        return False

    def get_rank_in_last_month(self):
        message = self.get_session_data()
        username = message[4]['username']
        message = self.send_and_receive("monthly_recap", {'username': username})
        if message[4]['status'] == 'ok':
            if message[4]['response']['ok']:
                last_rank = message[4]['response']['result']['badge']['current_name']
                current_xp = message[4]['response']['result']['badge']['current_xp']
                # if LOG_MORE:
                logger.success(f'[{self.client.num}] | {self.client.address} | {self.client.count_msg} | [Monthly recap] last_rank: {last_rank} current_xp: {current_xp}')
                return {'status': True, 'type': 'ok'}
        return {'status': False, 'type': 'error'}

    def first_login(self):
        message = self.get_session_data()
        status = message[4]['status']
        print(status)
        if status != 'unverified':
            return
        self.send_and_receive("verify_invite_code", {'code': "DRIPHAUS"})
        self.send_and_receive("set_onboarding_step", {'step': "create-profile"})
        message = self.get_session_data()
        username = message[4]['username']
        self.send_and_receive("edit_username", {'username': username})
        self.send_and_receive("edit_profile_image", {'asset_id': 'https://arweave.net/8tDZQ6G354jNDu9kDJx97buBc5xht6r-JfE3ET_Eonc?ext=jpg', 'default_image': True})
        self.send_and_receive("set_onboarding_step", {'step': "subscribe-to-channels"})
        message = self.send_and_receive("get_channels", {})
        results = message[4]['response']['results']
        recommended_slug_list = [i['slug'] for i in results if 'category_recommended' in i['tags']]
        for slug in recommended_slug_list:
            self.sub_channel(slug)
        self.send_and_receive("set_onboarding_step", {'step': "droplets-intro"})
        self.send_and_receive("set_onboarding_step", {'step': "purchase-droplets"})
        self.send_and_receive("get_droplet_purchase_options", {})
        self.send_and_receive("set_onboarding_step", {'step': "end-step"})
        self.send_and_receive("set_onboarding_step", {'step': "all-done"})
        self.send_and_receive("set_client_state", {'client_state': {'_': "D", 'hasSeenSecureIntroductoryModal': True}})
        message = self.get_session_data()
        status = message[4]['status']
        if status == 'unverified':
            logger.success(f'[{self.client.num}] | {self.client.address} | {self.client.count_msg} | [First login]')
            return True
        return False

    def check_can_like(self, droplet_ident: str):
        self.send("get_liked", {'droplet_ident': droplet_ident})
        while True:
            message = self.receive_last_msg()
            if message[3] == 'like' and message[4]['droplet_ident'] == droplet_ident:
                return not message[4]['active']  # инвертируем так как TRUE, если уже стоит лайк, а нам нужны там, где лайки отсутствуют

    def add_like(self, droplet_ident: str):
        if not self.check_can_like(droplet_ident):
            return {'status': False, 'type': 'already_liked'}
        message = self.send_and_receive("add_like", {'droplet_ident': droplet_ident})
        if message[4]['status'] == 'ok':
            if message[4]['response']['ok']:
                # if LOG_MORE:
                logger.success(f'[{self.client.num}] | {self.client.address} | {self.client.count_msg} | [Add Like] droplet_ident: {droplet_ident}')
                return {'status': True, 'type': 'ok'}
        return {'status': False, 'type': 'error'}

    def add_butch_likes(self, limit: int = 12, rarity: str = ''):
        count_need_like = randint(3, 5)
        count_liked = 0
        while True:
            droplet_ident_list = self.get_droplet_ident_list(limit, rarity, flag_only_unsecured=False)
            if not droplet_ident_list:
                logger.success(f'[{self.client.num}] | {self.client.address} | {self.client.count_msg} | Have no one nft for like')
                return
            for droplet_ident in droplet_ident_list:
                data = self.add_like(droplet_ident)
                if data['status']:
                    count_liked += 1
                if (count_need_like == count_liked) or (data['type'] == 'error'):
                    logger.success(f'[{self.client.num}] | {self.client.address} | {self.client.count_msg} | [Likes] count like: {count_liked}/{count_need_like}')
                    return

    def up_lvl_to_bronze(self):
        if self.check_xp_status(405):
            return True
        for rarity in ['rare', 'common']:
            while True:
                droplet_ident_list = self.get_droplet_ident_list(limit=12, rarity=rarity)
                if not droplet_ident_list:
                    break
                for droplet_ident in droplet_ident_list:
                    status = self.secure_droplet(droplet_ident)
                    if self.check_xp_status(405):
                        return True
                    if not status:
                        return

    def check_stop_need_rank(self):
        max_xp = 4302
        if self.client.num in ['slarck_40', 'slarck_50']:
            max_xp = 9900
        if self.check_xp_status(max_xp):  # если уже больше max_xp и выше то скипаем
            logger.warning(f'[{self.client.num}] | {self.client.address} | {self.client.count_msg} | [MAX RANK]')
            return True
        else:
            return False

    def get_droplet_balance(self):
        message = self.get_session_data()
        droplet_balance = message[4]['droplet_balance']
        logger.success(f'[{self.client.num}] | {self.client.address} | {self.client.count_msg} | [Droplet Balance] {droplet_balance}')
        return droplet_balance

    def check_xp_status(self, xp: int = 405):
        message = self.get_session_data()
        current_xp = message[4]['monthly_reward']['current_xp']
        if current_xp >= xp:
            logger.success(f'[{self.client.num}] | {self.client.address} | {self.client.count_msg} | [Current XP] {current_xp}')
            return True
        else:
            logger.info(f'[{self.client.num}] | {self.client.address} | {self.client.count_msg} | [Current XP] {current_xp}')
            return False

    def sub_list_channels(self):
        while True:
            message = self.send_and_receive("get_discover_creators", {"limit": 12, "include_subscribed": False})
            if message[4]['response']['ok']:
                results = message[4]['response']['results']
                if len(results) == 0:
                    if LOG_MORE:
                        logger.success(f'[{self.client.num}] | {self.client.address} | {self.client.count_msg} | [Sub List Channels] Subscribed to all channels')
                    return
                slug_list = [i['slug'] for i in results]
                for slug in slug_list:
                    status = self.sub_channel(slug)
                    if not status:
                        logger.error(f'[{self.client.num}] | {self.client.address} | {self.client.count_msg} | [Sub List Channels] Error')
                        return

    def sub_channel(self, slug: str) -> bool:
        message = self.send_and_receive("subscribe_channel", {'slug': slug})
        if message[4]['status'] == 'ok':
            if message[4]['response']['ok']:
                logger.success(f'[{self.client.num}] | {self.client.address} | {self.client.count_msg} | [Sub Channel] slug: {slug}')
                return True
        return False

    def get_droplet_ident_list(self, limit: int = 12, rarity: str = 'legendary', flag_only_unsecured=True):
        droplet_ident_list = []
        data = {
            "pubkey": self.client.address,
            "limit": limit,
            "offset": 0,
            "rarity": rarity,
            "type": "",
            "search": "",
            # "is_secured": False,
            "is_hidden": False
        }
        if flag_only_unsecured:
            data['is_secured'] = False
        message = self.send_and_receive("get_vault", data)
        if message[4]['response']['ok']:
            results = message[4]['response']['results']
            if len(results) == 0:
                logger.warning(
                    f'[{self.client.num}] | {self.client.address} | {self.client.count_msg} | [Secure All Collection] Secured to all collections')
                return []
            droplet_ident_list = [i['droplet_ident'] for i in results]
        return droplet_ident_list

    def secure_all_my_collections(self, limit: int = 12, rarity: str = 'legendary') -> dict:
        count_secure = 0
        while True:
            droplet_ident_list = self.get_droplet_ident_list(limit, rarity)
            if not droplet_ident_list:
                logger.success(f'[{self.client.num}] | {self.client.address} | {self.client.count_msg} | [Secure Droplet] count secure ({rarity}): {count_secure}')
                return {'count_secure': count_secure, 'status': 'empty'}
            for droplet_ident in droplet_ident_list:
                status = self.secure_droplet(droplet_ident)
                if not status:
                    logger.success(f'[{self.client.num}] | {self.client.address} | {self.client.count_msg} | [Secure Droplet] count secure ({rarity}): {count_secure}')
                    return {'count_secure': count_secure, 'status': 'some_error'}
                count_secure += 1

    def secure_droplet(self, droplet_ident: str) -> bool:
        message = self.send_and_receive("secure", {'droplet_ident': droplet_ident})
        if message[4]['status'] == 'ok':
            if message[4]['response']['ok']:
                if LOG_MORE:
                    logger.success(f'[{self.client.num}] | {self.client.address} | {self.client.count_msg} | [Secure Droplet] droplet_ident: {droplet_ident}')
                return True
            elif 'error' in message[4]['response'].keys():
                if 'Insufficient balance' in message[4]['response']['error']:
                    logger.warning(f'[{self.client.num}] | {self.client.address} | {self.client.count_msg} | [Secure All Collection] {message[4]["response"]["error"]}]')
                    return False
                else:
                    logger.error(f'[{self.client.num}] | {self.client.address} | {self.client.count_msg} | [Secure All Collection] {message[4]["response"]["error"]}]')
                    return False
        else:
            logger.error(f'[{self.client.num}] | {self.client.address} | {self.client.count_msg} | [Secure All Collection] status != "ok" {message[4]}]')
            return False

    def check_available_rarity_lockin(self) -> bool:
        message = self.get_session_data()
        next_at_ms = message[4]['rarity_lockin']['next_try_at_ms']
        if time.time() * 1000 > next_at_ms:
            return True
        next_time_date_dict = time_time_to_hms(next_at_ms)
        next_time_date_str = ' '.join([f'{int(v)}{k}' for k, v in next_time_date_dict.items()])
        logger.warning(f'[{self.client.num}] | {self.client.address} | {self.client.count_msg} | [Available Rarity Lockin] After {next_time_date_str}')
        return False

    def rarity_lockin(self):
        message = self.send_and_receive("play_lockin", {})
        if message[4]['response']['ok']:
            rarity = message[4]['response']['rarity']
            logger.success(f'[{self.client.num}] | {self.client.address} | {self.client.count_msg} | [Play Lockin] rarity: {rarity}')
        else:
            logger.error(f'[{self.client.num}] | {self.client.address} | {self.client.count_msg} | [Play Lockin] response: {message[4]["response"]}')

    def check_available_claim_droplets(self) -> bool:
        message = self.get_session_data()
        next_at_ms = message[4]['claim_config']['next_at_ms']
        if time.time() * 1000 > next_at_ms:
            return True
        next_time_date_dict = time_time_to_hms(next_at_ms)
        next_time_date_str = ' '.join([f'{int(v)}{k}' for k, v in next_time_date_dict.items()])
        logger.warning(f'[{self.client.num}] | {self.client.address} | {self.client.count_msg} | [Available Claim] After {next_time_date_str}')
        return False

    def claim_droplets(self) -> int:
        message = self.send_and_receive("claim_droplets", {})
        result = message[4]['response']['result']
        count_claimed = result['droplets'] * result['claim_multiplier']
        logger.success(f'[{self.client.num}] | {self.client.address} | {self.client.count_msg} | [claim_droplets] count: {count_claimed}')
        return count_claimed

    def get_session_data(self) -> list:
        data = {
            "bearer": self.client.bearer,
            "ua": self.client.ua,
        }
        self.send("phx_join", data)
        while True:
            message = self.receive_last_msg()
            if 'bearer' in message[4].keys() and message[3] == 'session':
                self.client.bearer = message[4]['bearer']
                if LOG_MORE:
                    logger.info(f'[{self.client.num}] | {self.client.address} | {self.client.count_msg} | [phx_join] msg: {message}')
                break
        return message

    def login(self) -> bool:
        self.get_session_data()
        if self.client.already_login:  # Если уже в Client есть валидный bearer не нужно логиниться
            return True

        signature = self.client.get_sign()
        data = {
            "signature": signature,
            "address": self.client.address,
        }
        message = self.send_and_receive("verify_pubkey", data)
        if message[4]['status'] == 'ok':
            if message[4]['response']['ok']:
                return True
        return False

    def logout(self):
        self.send("logout", {})
        logger.info(f'[{self.client.num}] | {self.client.address} | {self.client.count_msg} | [logout]')

    def send_and_receive(self, name_func: str, data: dict) -> list:
        self.send(name_func, data)
        message = self.receive_count_msg(self.client.count_msg)
        if LOG_MORE:
            logger.info(f'[{self.client.num}] | {self.client.address} | {self.client.count_msg} | [{name_func}] msg: {message}')
        return message

    def send(self, name_func: str, data: dict) -> None:
        self.client.count_msg += 1
        data = ["3", self.client.count_msg, "drip", name_func, data]
        msg = json.dumps(data)
        self.client.ws.send(msg)

    def receive_count_msg(self, count_msg: int) -> list:
        while True:
            message = self.receive_last_msg()
            if message[1] == count_msg:
                break
        return message

    def receive_last_msg(self) -> list:
        message_str = self.client.ws.recv()
        message = json.loads(message_str)
        # logger.info(f'[{self.client.num}] | {self.client.address} | {self.client.count_msg} | [LAST MSG] msg: {message}')
        return message
