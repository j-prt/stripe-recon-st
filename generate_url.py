"""Reconcile Stripe deposits with Commerce7 orders.

Input args:
    - [1]  Path to Stripe csv

Output: Niche C7 URL to use to find the correct date range of orders."""

import csv
import sys
from datetime import datetime, timedelta

DELTA_MIN = 5
NICHE_URL = 'https://niche-wine-company.admin.platform.commerce7.com/store/order?orderPaidDate=btw:'


def generate(f):
    # Assumes it receives a file-like object
    reader = csv.reader(f)

    # Skip header
    next(reader)

    # Get the first date
    start = datetime.strptime(next(reader)[2], '%Y-%m-%d %H:%M')

    for row in reader:
        # Timestamp at index 2 of the Stripe file
        last = row

    finish = datetime.strptime(last[2], '%Y-%m-%d %H:%M')

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
