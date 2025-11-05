from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import numpy as np

MAX_DIFF_SECONDS = 100


def compare(left, right):
    time_diff = abs((left[1] - right[1]).total_seconds())
    return left[0] == right[0] and time_diff < MAX_DIFF_SECONDS


def extract_null_info(df):
    info_to_match = []
    for row in df.iterrows():
        # Payment total (not deposit)
        amt = row[1]['Amount']

        # Stripe timestamps are in UTC
        timestamp = row[1]['Created']
        timestamp = datetime.strptime(timestamp, '%Y-%m-%d %H:%M')
        timestamp = timestamp.replace(tzinfo=timezone.utc)

        info_to_match.append((amt, timestamp))

    return info_to_match


def find_orders(to_match, row):
    total = row['Total']
    charge_time = row['Order Paid Date']

    # Convert to UTC
    date = datetime.strptime(charge_time, '%Y-%m-%d %H:%M:%S')
    tz = ZoneInfo('America/Vancouver')
    date = date.replace(tzinfo=tz).astimezone(timezone.utc)

    # Compare with the external list holding the null stripe info
    for pair in to_match:
        if compare((total, date), pair):
            return True

    return False


def clean_c7(stripe, c7_df):
    # Prep
    deduped = c7_df[~c7_df['Order Number'].duplicated()]
    non_null = stripe[~stripe.Description.isna()]
    null = stripe[stripe.Description.isna()]

    # Orders already available
    orders = non_null.Description.str.split().apply(lambda x: x[-1]).astype(int).values

    # Extract info from the null rows
    to_match = extract_null_info(null)

    # Pull out the remaining order numbers
    more_orders = deduped[
        deduped.apply(lambda row: find_orders(to_match, row), axis=1)
    ]['Order Number'].values

    all_orders = np.concatenate((orders, more_orders))

    return c7_df[c7_df['Order Number'].isin(all_orders)]
