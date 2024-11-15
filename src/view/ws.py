import json
import time
from random import randint

from loguru import logger

from config import LOG_MORE
from view.helper import *


class WS:
    def __init__(self, client):
        super().__init__()
        self.client = client

    def start(self):
        if not self.login():
            logger.error(f'[{self.client.num}] | {self.client.address} | Error in login')
        self.up_lvl_to_bronze()
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
        self.get_droplet_balance()

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
                        break

    def get_droplet_balance(self):
        message = self.get_session_data()
        droplet_balance = message[4]['droplet_balance']
        logger.success(f'[{self.client.num}] | {self.client.address} | {self.client.count_msg} | [Droplet Balance] {droplet_balance}')

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

    def sub_channel(self,slug: str) -> bool:
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
