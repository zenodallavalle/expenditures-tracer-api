from datetime import datetime
import requests

import tz

BASE_URL = 'https://api-m.paypal.com'


class GenericError(Exception):
    def __init__(self, *args: object, r=None) -> None:
        self.r = r
        super().__init__(*args)


class PayPal:
    def __init__(self, client_id: str, client_secret: str) -> None:
        self._client_id = client_id
        self._client_secret = client_secret
        self._access_token = None

    def _login(self):
        r = requests.post(
            'https://api-m.paypal.com/v1/oauth2/token',
            data={'grant_type': 'client_credentials'},
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            auth=(
                'Ae3C8qjAV9xopiti7KxxKysEKjpMCzSSqsDG9DjRnqmSlIY9QU-7nJPXxfWapB1MMH6mTX-XoOjqWZ8K',
                'EKFFAm7HX9YMtjhTvP8kouuZ_nIWncdH8w09p9hZ9r5Z8iXjueuzWFbiLFznsr04wgecLDUckuzhYMGR',
            ),
        )
        if r.status_code != 200:
            raise GenericError(r=r)
        self._access_token = r.json()['access_token']

    def get_transactions(
        self,
        start_date: datetime,
        end_date: datetime,
        transaction_status: str,
        page_size=500,
        fields='all',
        return_raw=False,
    ):
        if self._access_token is None:
            self._login()
        r = requests.get(
            BASE_URL + '/v1/reporting/transactions',
            headers={
                'Content-Type': 'application/json',
                'Authorization': 'Bearer {}'.format(self._access_token),
            },
            params={
                'start_date': tz.to_iso(start_date),
                'end_date': tz.to_iso(end_date),
                'transaction_status': transaction_status,
                'page_size': page_size,
                'fields': fields,
            },
        )
        if r.status_code != 200:
            raise GenericError(r=r)
        if return_raw:
            return r.json()
        transactions_details = r.json()['transaction_details']
        transactions = []
        for transaction_details in transactions_details:
            details = transaction_details['transaction_info']
            id = details.get('transaction_id', None)
            account = details.get('paypal_account_id', None)
            date = details.get('transaction_initiation_date', None)
            amount = details.get('transaction_amount', None)
            currency_code = amount.get('currency_code', None)
            value = amount.get('value', None)
            transaction_status = details.get('transaction_status', None)
            transaction_note = details.get('transaction_note', None)
            transactions.append(
                {
                    'id': id,
                    'account': account,
                    'date': date,
                    'currency': currency_code,
                    'value': value,
                    'status': transaction_status,
                    'note': transaction_note,
                }
            )
        return transactions
