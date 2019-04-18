from personalcapital import PersonalCapital, RequireTwoFactorException, TwoFactorVerificationModeEnum
import getpass
import json
import logging
import os
from datetime import datetime, timedelta, date

# Python 2 and 3 compatibility
if hasattr(__builtins__, 'raw_input'):
    input = raw_input

class PewCapital(PersonalCapital):
    """
    Extends PersonalCapital to save and load session
    So that it doesn't require 2-factor auth every time
    """
    def __init__(self):
        PersonalCapital.__init__(self)
        self.__session_file = 'session.json'

    def load_session(self):
        try:
            with open(self.__session_file) as data_file:    
                cookies = {}
                try:
                    cookies = json.load(data_file)
                except ValueError as err:
                    logging.error(err)
                self.set_session(cookies)
        except IOError as err:
            logging.error(err)

    def save_session(self):
        with open(self.__session_file, 'w') as data_file:
            data_file.write(json.dumps(self.get_session()))

def get_email():
    email = os.getenv('PEW_EMAIL')
    if not email:
        print('You can set the environment variables for PEW_EMAIL and PEW_PASSWORD so the prompts don\'t come up every time')
        return input('Enter email:')
    return email

def get_password():
    password = os.getenv('PEW_PASSWORD')
    if not password:
        return getpass.getpass('Enter password:')
    return password

def print_header(msg):
    print('-' * 79)
    print(msg)
    print('-' * 79)

def print_expenses(transactions_list):
    for transaction in transactions_list:
        if 'merchant' not in transaction:
            print('{},{},{}'.format(transaction['transactionDate'],
                    transaction['amount'],
                    transaction['description']))
        else:
            print('{},{},{}'.format(transaction['transactionDate'],
                    transaction['amount'],
                    transaction['merchant']))

def main():
    #email, password = get_email(), get_password()
    email, password = 'willyiwei@gmail.com', get_password()
    pc = PewCapital()
    pc.load_session()

    try:
        pc.login(email, password)
    except RequireTwoFactorException:
        pc.two_factor_challenge(TwoFactorVerificationModeEnum.SMS)
        pc.two_factor_authenticate(TwoFactorVerificationModeEnum.SMS, input('code: '))
        pc.authenticate_password(password)

    accounts_response = pc.fetch('/newaccount/getAccounts')
    
    today_date = date.today()
    #today_date = date(2018, 8, 31)
    date_format = '%Y-%m-%d'
    #if today_date.day > 25:
    #    today_date += timedelta(7)
    start_date = today_date.replace(day=1).strftime(date_format) # always starts from day 1 of this month.
    end_date = today_date.strftime(date_format)
    transactions_response = pc.fetch('/transaction/getUserTransactions', {
        'sort_cols': 'transactionTime',
        'sort_rev': 'true',
        'page': '0',
        'rows_per_page': '100',
        'startDate': start_date,
        'endDate': end_date,
        'component': 'DATAGRID'
    })
    pc.save_session()

    accounts = accounts_response.json()['spData']
    print('Networth: {0}'.format(accounts['networth']))
    transactions = transactions_response.json()['spData']
    print('The transaction details between {0} and {1}'.format(transactions['startDate'], transactions['endDate']))
    chase_freedom_transactions = []
    chase_csp_transactions = []
    chase_marriott_transactions = []
    amex_bcp_transactions = []
    discover_card_transactions = []
    amazon_store_card_transactions = []
    for transaction in transactions['transactions']:
        if transaction['accountName'] == 'Chase Freedom' and transaction['isSpending']:
            chase_freedom_transactions.append(transaction)
        if transaction['accountName'] == 'Chase Sapphire Preferred' and transaction['isSpending']:
            chase_csp_transactions.append(transaction)
        if transaction['accountName'] == 'Chase Marriott' and transaction['isSpending']:
            chase_marriott_transactions.append(transaction)
        if 'Blue Cash Preferred' in transaction['accountName'] and transaction['isSpending']: # there are two BCP accounts
            amex_bcp_transactions.append(transaction)
        if transaction['accountName'] == 'Discover Card' and transaction['isSpending']:
            discover_card_transactions.append(transaction)
        if 'Amazon Prime Store Card' in transaction['accountName'] and transaction['isSpending']:
            amazon_store_card_transactions.append(transaction)
    # Chase Freedom
    print_header('Chase Freedom')
    print_expenses(chase_freedom_transactions)
    # Chase Sapphire Preferred
    print_header('Chase Sapphire Preferred')
    print_expenses(chase_csp_transactions)
    # Chase Marriott
    print_header('Chase Marriott')
    print_expenses(chase_marriott_transactions)
    # American Express Blue Cash Perferred
    print_header('American Express Blue Cash Perferred')
    print_expenses(amex_bcp_transactions)
    # Discover Card
    print_header('Discover Card')
    print_expenses(discover_card_transactions)
    # Amazon Store Card
    print_header('Amazon Store Card')
    print_expenses(amazon_store_card_transactions)
    

if __name__ == '__main__':
    main()
