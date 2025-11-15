"""Reconcile Stripe deposits with Commerce7 orders.

Input args:
    - [1]  Path to Stripe csv

Output: Niche C7 URL to use to find the correct date range of orders."""

import sys
from datetime import datetime, timedelta

import pandas as pd

DELTA_MIN = 5
NICHE_URL = 'https://niche-wine-company.admin.platform.commerce7.com/store/order?orderPaidDate=btw:'


def generate(f):
    # Assumes it receives a file-like object
    df = pd.read_csv(f)

    df['Created'] = pd.to_datetime(df['Created'], format='%Y-%m-%d %H:%M')

    start = df['Created'].min()
    finish = df['Created'].max()

    delta = timedelta(minutes=DELTA_MIN)

    # Format used in C7: 2025-06-24T00:00:00.000Z
    start = datetime.strftime(start - delta, '%Y-%m-%dT%H:%M:%S.000Z')
    finish = datetime.strftime(finish + delta, '%Y-%m-%dT%H:%M:%S.000Z')

    return f'{NICHE_URL}{start}|{finish}'


if __name__ == '__main__':
    path = sys.argv[1]
    with open(path) as f:
        url = generate(f)
    print(url)
