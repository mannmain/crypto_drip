import base64
import time

import base58
from loguru import logger
from config import LOG_MORE
from view.helper import *
from solana.rpc.api import Client
from solana.rpc.commitment import Commitment, Confirmed
from solana.rpc.types import TxOpts
from solders.keypair import Keypair
from solders.message import MessageV0
from solders.system_program import TransferParams, transfer
from solders.transaction import VersionedTransaction

RPC_ENDPOINT = "https://api.mainnet-beta.solana.com"


class Transfer:
    def __init__(
            self,
            num_sender: str | int,
            num_receiver: str | int,
    ):
        self.num_sender = str(num_sender)
        self.num_receiver = str(num_receiver)

    def transfer_with_middle(
            self,
            pk_sender: str,
            pk_receiver: str,
            sol_transfer: int,
    ):
        keypair_receiver = Keypair.from_base58_string(pk_receiver)
        if self.check_balance(keypair_receiver, 1):
            return True
        # keypair_middle_first = Keypair.from_base58_string('c4hCT5ADbxbmdwUhniUthTqXrgUKCEktRtN5XjSFCid1PWanBaua7QuKAbo7a4UJqRJrRw9ucTAocqjLb2S8UA3')
        keypair_middle_first = Keypair()
        private_key_middle_1 = base58.b58encode(bytes(keypair_middle_first.to_bytes_array())).decode('utf-8')
        # keypair_middle_second = Keypair.from_base58_string('61aLev12tewgArjsidkSMSF23i1Kuyr6R3USLQ1TMsJakihf15pRb5bVGvFVcXLnWY92QxPUTYiyrKdcLUn8GA4P')
        keypair_middle_second = Keypair()
        private_key_middle_2 = base58.b58encode(bytes(keypair_middle_second.to_bytes_array())).decode('utf-8')

        logger.info(f'----------------- [Start] | Sender -> {keypair_middle_first.pubkey()} -> {keypair_middle_second.pubkey()} -> {keypair_receiver.pubkey()}')

        logger.info(f'[{self.num_sender} -> {self.num_receiver}] | First Middle https://solscan.io/account/{keypair_middle_first.pubkey()} {private_key_middle_1=}')
        logger.info(f'[1 tnx] | Sender -> https://solscan.io/account/{keypair_middle_first.pubkey()}')
        self.transfer_to_wallet(pk_sender, private_key_middle_1, sol_transfer)
        # input('1: ')

        logger.info(f'[{self.num_sender} -> {self.num_receiver}] | Second Middle https://solscan.io/account/{keypair_middle_second.pubkey()} {private_key_middle_2=}')
        sol_transfer = self.wait_and_get_balance_sol_max_to_send('2', keypair_middle_first)
        logger.info(f'[2 tnx] | https://solscan.io/account/{keypair_middle_first.pubkey()} -> https://solscan.io/account/{keypair_middle_second.pubkey()}')
        self.transfer_to_wallet(private_key_middle_1, private_key_middle_2, sol_transfer)
        # input('2: ')

        sol_transfer = self.wait_and_get_balance_sol_max_to_send('3', keypair_middle_second)
        logger.info(f'[3 tnx] | https://solscan.io/account/{keypair_middle_second.pubkey()} -> https://solscan.io/account/{keypair_receiver.pubkey()}')
        self.transfer_to_wallet(private_key_middle_2, pk_receiver, sol_transfer)
        logger.info(f'----------------- [END] | Sender -> {keypair_receiver.pubkey()}')
        # input('3: ')

    def withdraw_all_with_middle(
            self,
            pk_sender: str,
            pk_receiver: str,
    ):
        keypair_sender = Keypair.from_base58_string(pk_sender)
        if not self.check_balance(keypair_sender, 1):  # если баланс не больше 0, то есть 0, значит акк пустой скип
            return True
        # keypair_middle_first = Keypair.from_base58_string('c4hCT5ADbxbmdwUhniUthTqXrgUKCEktRtN5XjSFCid1PWanBaua7QuKAbo7a4UJqRJrRw9ucTAocqjLb2S8UA3')
        keypair_middle_first = Keypair()
        private_key_middle_1 = base58.b58encode(bytes(keypair_middle_first.to_bytes_array())).decode('utf-8')
        # keypair_middle_second = Keypair.from_base58_string('61aLev12tewgArjsidkSMSF23i1Kuyr6R3USLQ1TMsJakihf15pRb5bVGvFVcXLnWY92QxPUTYiyrKdcLUn8GA4P')
        keypair_middle_second = Keypair()
        private_key_middle_2 = base58.b58encode(bytes(keypair_middle_second.to_bytes_array())).decode('utf-8')

        logger.info(f'----------------- [Start] | {keypair_sender.pubkey()} -> {keypair_middle_first.pubkey()} -> {keypair_middle_second.pubkey()} -> Sender')

        logger.info(f'[{self.num_sender} -> {self.num_receiver}] | First Middle https://solscan.io/account/{keypair_middle_first.pubkey()} {private_key_middle_1=}')
        logger.info(f'[1 tnx] | {keypair_sender.pubkey()} -> https://solscan.io/account/{keypair_middle_first.pubkey()}')
        sol_transfer = self.wait_and_get_balance_sol_max_to_send('1', keypair_sender)
        self.transfer_to_wallet(pk_sender, private_key_middle_1, sol_transfer)
        # input('1: ')

        logger.info(f'[{self.num_sender} -> {self.num_receiver}] | Second Middle https://solscan.io/account/{keypair_middle_second.pubkey()} {private_key_middle_2=}')
        sol_transfer = self.wait_and_get_balance_sol_max_to_send('2', keypair_middle_first)
        logger.info(f'[2 tnx] | https://solscan.io/account/{keypair_middle_first.pubkey()} -> https://solscan.io/account/{keypair_middle_second.pubkey()}')
        self.transfer_to_wallet(private_key_middle_1, private_key_middle_2, sol_transfer)
        # input('2: ')

        sol_transfer = self.wait_and_get_balance_sol_max_to_send('3', keypair_middle_second)
        logger.info(f'[3 tnx] | https://solscan.io/account/{keypair_middle_second.pubkey()} -> Sender')
        self.transfer_to_wallet(private_key_middle_2, pk_receiver, sol_transfer)
        logger.info(f'----------------- [END] | {keypair_sender.pubkey()} -> Sender')
        # input('3: ')

    def wait_and_get_balance_sol_max_to_send(self, num_txn, keypair):
        client = Client(RPC_ENDPOINT, commitment=Commitment("confirmed"), timeout=30)
        while True:
            sol_transfer = client.get_balance(keypair.pubkey()).value
            if sol_transfer > 0:
                break
            logger.info(f'[{num_txn} tnx] | wait while sol_transfer == 0')
            time.sleep(2)
        sol_transfer -= 5_000
        return sol_transfer

    def transfer_to_wallet(
            self,
            pk_sender: str,
            pk_receiver: str,
            sol_transfer: int,
    ):
        keypair_sender = Keypair.from_base58_string(pk_sender)
        keypair_receiver = Keypair.from_base58_string(pk_receiver)
        client = Client(RPC_ENDPOINT, commitment=Commitment("confirmed"), timeout=30)
        sol_value_before_transfer = client.get_balance(keypair_receiver.pubkey()).value

        # sol_transfer = client.get_balance(keypair_sender.pubkey()).value
        # input(sol_transfer)
        # if sol_transfer == 0:
        #     return
        # sol_transfer -= 5_000

        while True:
            try:
                ix = transfer(
                    TransferParams(
                        from_pubkey=keypair_sender.pubkey(), to_pubkey=keypair_receiver.pubkey(), lamports=sol_transfer
                    )
                )
                blockhash = client.get_latest_blockhash().value.blockhash
                msg = MessageV0.try_compile(
                    payer=keypair_sender.pubkey(),
                    instructions=[ix],
                    address_lookup_table_accounts=[],
                    recent_blockhash=blockhash,
                )
                signed_txn = VersionedTransaction(msg, [keypair_sender])

                opts = TxOpts(skip_preflight=False, preflight_commitment=Confirmed, skip_confirmation=False)

                result = client.send_transaction(signed_txn, opts)
                tx_signature = result.value
                solscan_url = f"https://solscan.io/tx/{tx_signature}"
                logger.success(f'[{self.num_sender} -> {self.num_receiver}] | {keypair_sender.pubkey()} -> https://solscan.io/account/{keypair_receiver.pubkey()} | send | {solscan_url}')
                while True:
                    time.sleep(2)
                    if self.check_balance(keypair_receiver, sol_value_before_transfer + sol_transfer):
                        break
                    logger.info(f'Ждем транзакцию {solscan_url}')
                return
            except Exception as e:
                # logger.error(f'[{self.num_sender} -> {self.num_receiver}] | Global Error: {e}')
                time.sleep(5)
                print("Global Error:", [e.__str__()])
                if 'Blockhash not found' in str(e):
                    continue
                for _ in range(5):
                    if self.check_balance(keypair_receiver, sol_value_before_transfer + sol_transfer):
                        return
                    time.sleep(5)
                continue
                status = input('CHECK WALLET enter if all nice and write smth if try again: ')
                if not status:
                    return

    def check_balance(self, keypair, balance_value: int):
        client = Client(RPC_ENDPOINT, commitment=Commitment("confirmed"), timeout=30)
        balance = client.get_balance(keypair.pubkey())
        if balance.value > balance_value - 1:
            logger.info(f'[{self.num_sender} -> {self.num_receiver}] | {keypair.pubkey()} | Balance | {balance.value / 1_000_000_000} sol')
            return True
        else:
            logger.warning(f'[{self.num_sender} -> {self.num_receiver}] | {keypair.pubkey()} | Balance | {balance.value / 1_000_000_000} sol')
            return False

