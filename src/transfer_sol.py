from view.transfer_to_all_accs import Transfer
import pandas as pd


def main():
    acc_with_balance = ''
    main_acc = {
        'private_key': acc_with_balance,
        'num': 'seder'
    }
    # creds_df = pd.read_excel('creds/creds_new_slarck.xlsx', sheet_name='Лист1', dtype=str)
    creds_df = pd.read_excel('creds/creds_crypto_soroka.xlsx', sheet_name='Лист1', dtype=str)
    result = creds_df.to_dict(orient='records')
    slave_acc_list = [i for i in result if str(i['transfer']) == '1']
    for slave_acc in slave_acc_list:
        Transfer(num_sender=main_acc['num'], num_receiver=slave_acc['num']).transfer_with_middle(
            pk_sender=main_acc['private_key'],
            pk_receiver=slave_acc['private_key'],
            sol_transfer=9_000_000,
        )  # это для рассылки на все кошельки
        Transfer(num_sender=slave_acc['num'], num_receiver=main_acc['num']).withdraw_all_with_middle(
            pk_sender=slave_acc['private_key'],
            pk_receiver=main_acc['private_key'],
        )  # это для сбора всех sol с кошельков


if __name__ == '__main__':
    main()
