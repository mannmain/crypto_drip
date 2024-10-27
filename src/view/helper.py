import random
import time
import uuid


def get_uuid4():
    random_uuid = str(uuid.uuid4())
    return random_uuid


def get_user_agent():
    random_version = f"{random.uniform(520, 540):.2f}"
    return (f'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/{random_version}'
            f' (KHTML, like Gecko) Chrome/121.0.0.0 Safari/{random_version} Edg/121.0.0.0')


def time_time_to_hms(next_at_ms):
    different = next_at_ms / 1000 - time.time()
    next_time_date_dict = {
        'h': different // 3600,
        'm': different % 3600 // 60,
        's': different % 3600 % 60 % 60
    }
    return next_time_date_dict
