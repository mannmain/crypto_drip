import websocket
from loguru import logger
from solana.transaction import Keypair
from view.helper import *
import random
import string


class Client:

    def __init__(
            self,
            private_key: str,
            num: str | int = 1,
            proxy: str | None = None,
            bearer: str | None = None,
            **kwargs
    ):
        self.count_msg = 0
        self.num = str(num)
        drip_ws_url = "wss://drip.haus/drip/websocket?vsn=2.0.0"
        self.ws = websocket.WebSocket()
        self.proxy_url = proxy
        self.ua = get_user_agent()
        if 'http://' not in self.proxy_url:
            self.proxy_url = f'http://{self.proxy_url}'
        for _ in range(20):
            try:
                self.ws.connect(drip_ws_url, **self.get_kwargs_proxy())
                break
            except Exception as ex:
                print(f'error proxy: {ex}')
                logger.error(f'[{self.num}] | error proxy: {ex}')
                # time.sleep(10)
        else:
            raise Exception(f'[{self.num}] bad proxy {self.proxy_url}')
        self.pk = private_key
        self.address = str(Keypair.from_base58_string(self.pk).pubkey())
        self.bearer = get_uuid4()
        self.already_login = False
        if bearer:
            self.bearer = bearer
            self.already_login = True

    def get_nano_id(self, size=21):
        chars = string.ascii_lowercase + string.ascii_uppercase + '0123456789-_'
        return ''.join(random.choice(chars) for _ in range(size))

    def get_sign(self) -> str:
        keypair = Keypair.from_base58_string(self.pk)
        keypair.pubkey()
        request_id = int(self.bearer.split('-')[0], 16) % 2345678 % 45678 % 8653
        msg = (f'drip.haus wants you to sign in with your Solana account:\n{self.address}\n\n'
               f'Sign in to DRiP\n\nRequest ID: {request_id}:{self.bearer}')
        signature = str(keypair.sign_message(msg.encode()))
        return signature

    def get_kwargs_proxy(self) -> dict:
        kwargs_proxy = {}
        if self.proxy_url:
            if '://' in self.proxy_url:
                proxy_type, proxy_without_type = self.proxy_url.split('://')
            else:
                proxy_type, proxy_without_type = 'http', self.proxy_url
            user_password, ip_port = proxy_without_type.split('@')
            user, password = user_password.split(':')
            ip, port = ip_port.split(':')
            kwargs_proxy = {
                'http_proxy_host': ip,
                'http_proxy_port': port,
                'proxy_type': proxy_type,
                'http_proxy_auth': (user, password),
            }
        return kwargs_proxy
