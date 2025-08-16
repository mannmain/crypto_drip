# Crypto Drip — automation for DRiP (Solana)

Автоматизация действий на **drip.haus** через WebSocket с авторизацией подписью Solana-ключа. Скрипт умеет логиниться, забирать «sponsored» и обычные дроплеты, фиксировать редкость (rarity lock‑in), подписываться на каналы и ставить лайки батчами, а также «прятать» коллекции. Есть интеграция с Telegram для уведомлений и отдельный вспомогательный скрипт для рассылки/сбора SOL между кошельками.

> ⚠️ Используйте только для своих аккаунтов и с пониманием рисков. Храните приватные ключи безопасно.

---

## 📦 Что внутри

```
.
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── docker/
│   └── main.sh                  # точка входа в контейнере
└── src/
    ├── config.py                # .env-параметры (логгинг, Telegram)
    ├── main.py                  # основной цикл обработки всех аккаунтов из creds.xlsx
    ├── transfer_sol.py          # вспомогательный скрипт переводов SOL
    ├── tg/
    │   └── notification.py      # отправка сообщений/файлов в Telegram
    └── view/
        ├── client.py            # клиент WebSocket к wss://drip.haus/drip/websocket?vsn=2.0.0
        ├── ws.py                # ядро автоматизации (методы ниже)
        ├── helper.py            # утилиты (uuid, user-agent, таймеры)
        └── transfer_to_all_accs.py  # реализация транзакций SOL через промежуточные кошельки
```

### Основные возможности (`src/view/ws.py`)
- `login()`, `first_login()` — вход через подпись сообщения Solana‑ключом.
- `get_sponsoreds()`, `claim_sponsored()` — поиск и клейм «спонсорских» дропов.
- `check_available_claim_droplets()`, `claim_droplets()` — клейм обычных дроплетов.
- `check_available_rarity_lockin()`, `rarity_lockin()` — фиксация редкости (lock‑in).
- `sub_list_channels()`, `sub_channel()` — подписка на каналы.
- `check_can_like()`, `add_like()`, `add_butch_likes()` — лайки (включая батчи).
- `secure_droplet()`, `secure_all_my_collections()` — «спрятать» отдельный дроп или все коллекции.
- `check_xp_status(target)`, `get_rank_in_last_month()` — проверки XP/рейтинга.
- `buy_droplets()` — покупка дроплетов (при необходимости).
- Дополнительно: `check_unlock_price()`, `check_collection_on_acc()`, `up_lvl_to_bronze()` и др.
- RPC по умолчанию: `https://api.mainnet-beta.solana.com` (см. код).

---

## 🔧 Подготовка окружения

### Требования
- Python 3.10+ **или** Docker/Docker Compose
- Таблица с учетками в `src/creds/creds.xlsx` (формат ниже)
- Файл `.env` в корне проекта для конфигурации

### .env (пример)
Переименуйте `.env.example` как `.env`:
- [Перейти к .env.example](.env.example)

```dotenv
# Логирование
LOG_MORE=1

# Telegram (опционально)
TG_API_TOKEN=123456:ABCDEF-your-telegram-bot-token
TG_GROUP_ID=-1001234567890
TG_NAME_PARSE=[CRYPTO_DRIP]
```

### Файл аккаунтов `src/creds/creds.xlsx`
Лист **Лист1**, колонки (минимум):
- `num` — метка/номер аккаунта (строка или число).
- `private_key` — приватный ключ Solana **в Base58**.
- `proxy` — строка прокси, опционально. Формат:
  - `http://user:pass@ip:port`
- `status` — 1/0 для включения/отключения аккаунта (если используете логику статуса).

Готовый шаблон:
- [Перейти к creds_template.xlsx](example_files/creds_template.xlsx)

Поместите файл по пути: `src/creds/creds.xlsx`.

---

## ▶️ Запуск

### Вариант 1 — Docker
1) Подготовьте `.env` и `src/creds/creds.xlsx`.
2) (Опционально) отредактируйте монтирование в `docker-compose.yml` — по умолчанию ожидается, что **хостовая** папка с кредами находится в `/home/crypto_drip/src/creds`:
```yaml
    volumes:
      - /home/crypto_drip/src/creds:/project/src/creds
```
3) Соберите и запустите:
```bash
docker-compose up --build -d
```
Остановить: `docker-compose down`.

> Контейнер запускает `python3 -u src/main.py` и крутит цикл обработки. В коде заложены паузы между волнами (около 6 часов).

### Вариант 2 — Локально (без Docker)
1) Установите зависимости (`requirements.txt`):
```bash
python -m venv .venv
source .venv/bin/activate             # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```
2) Запустите:
```bash
python src/main.py
```

---

## 🪙 Переводы SOL (опционально)

Скрипт `src/transfer_sol.py` использует `view/transfer_to_all_accs.py` для рассылки SOL на множество кошельков через один/два «промежуточных» кошелька и обратного сбора средств.
- Исходные данные берёт из Excel (см. пример в коде — замените на свой файл/лист).
- Методы: `transfer_with_middle()` — разослать, `withdraw_all_with_middle()` — собрать обратно.
- RPC: `https://api.mainnet-beta.solana.com` (можно заменить в коде).

**Важно:** операции на mainnet необратимы. Тщательно тестируйте на небольших суммах.

---

## 📡 Telegram‑уведомления

Модуль `src/tg/notification.py` отправляет сообщения/файлы в чат/группу по Bot API.
- Настройте `TG_API_TOKEN`, `TG_GROUP_ID`, `TG_NAME_PARSE` в `.env`.
- В коде используются повторные попытки при ошибках сети/429.

---

## 🧩 Как это работает (в двух словах)

1. Для каждой строки `creds.xlsx` создаётся `Client` (pk, proxy, num).
2. Через `client.ws` формируется соединение с `wss://drip.haus/drip/websocket?vsn=2.0.0` и производится логин подписью Solana‑ключа.
3. Класс `WS` выполняет последовательность действий: клейм дропов, lock‑in редкости, подписки/лайки, «сокрытие» коллекций и пр. Логика учитывает доступность операцией (чтобы не дублировать запросы).
4. Отчёты и статусы (в т.ч. ошибки) отправляются в Telegram (если настроено).

---

## Контакты

tg: [mann_main](https://t.me/mann_main)

---

## Донаты

EVM: 0x9Dd929Fe4F55b2c21Ca50e90B0bEc51890A4FEB8

SOL: BvHtqGMC77bbhiheWpLenNngiAHuKkyo3WZgZ7mNGTsZ

---

## Дисклеймер

Все материалы и программное обеспечение предоставляются "как есть" без каких-либо явных или подразумеваемых гарантий. Автор не несет ответственности за любые убытки, убытки, повреждения или другие последствия, возникшие в результате использования или невозможности использования данного программного обеспечения. Использование происходит на собственный риск.