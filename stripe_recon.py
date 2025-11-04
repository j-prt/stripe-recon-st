"""Reconcile Stripe deposits with Commerce7 orders.

Input args:
    - [1]  Path to Stripe csv
    - [2:] One or more paths to Comerce7 orders

Output: <date>.csv written to active directory. <date> is derived from name of Stripe path.

If debug flag is set, prints product, taxes, and summary dataframes to console instead."""

import argparse

import numpy as np
import pandas as pd


def parse_args():
    parser = argparse.ArgumentParser(
        description='Process paths for reconciling Stripe with C7'
    )

    # Debug flag
    parser.add_argument(
        '-d', '--debug', action='store_true', help='Enable debug output'
    )

    # Stripe path (always 1)
    parser.add_argument('stripe', help='Path to the Stripe file')

    # C7 paths (one or more)
    parser.add_argument('commerce7', nargs='+', help='Paths to Commerce7 files')

    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    print(args)


def process_products(df: pd.DataFrame) -> pd.DataFrame:
    """Calculates sold product counts and subtotals (by item)
    and returns data as a DataFrame with columns:

    | Product | Count | Subtotal |"""

    unique_products = df['Product Title'].unique()

    # Get the count and subtotal for each unique product
    product_totals = []
    for product in unique_products:
        sub_df = df[df['Product Title'] == product]
        count = sub_df['Quantity'].sum()
        subtotal = sub_df['Product SubTotal'].sum().round(2)
        product_totals.append([product, count, subtotal])

    # Prep return df
    product_headers = ['Products', 'Count', 'Subtotal']
    product_df = pd.DataFrame(product_totals, columns=product_headers)

    return product_df


def process_taxes(df: pd.DataFrame) -> pd.DataFrame:
    """Calculates tax totals by tax type (and shipping)
    and returns data as a DataFrame of shape:

      <index>  |  Count  |
    | Tax Type | <value> |"""

    taxes = df[~df['Order Number'].duplicated()]

    # Individual tax categories
    shipping = taxes['Shipping Total'].sum().round(2)
    gst = taxes['Tax: GST'].sum().round(2)
    pst = taxes['Tax: PST'].sum().round(2)
    alberta = taxes['Tax: Alberta Admin Fee'].sum().round(2)
    other = (
        taxes[
            [
                'Tax: Tax',
                'Tax: CRV',
                'Tax: Maine Bottle Bill',
                'Tax: Wholesale',
                'Tax: HST',
                'Tax: QST',
                'Tax: Other',
            ]
        ]
        .sum()
        .sum()
        .round(2)
    )
    bottle = taxes['Bottle Deposit Total'].sum().round(2)

    # Make the return df
    tax_totals = [shipping, gst, pst, alberta, other, bottle]
    taxes_headers = ['Count']
    taxes_rows = [
        'Shipping',
        'GST',
        'PST',
        'Alberta Charge',
        'Other Taxes',
        'Bottle Deposit',
    ]
    taxes_df = pd.DataFrame(tax_totals, index=taxes_rows, columns=taxes_headers)

    return taxes_df


def read_stripe(path: str) -> tuple[np.float64, np.float64]:
    """Read the stripe file and returns"""
    stripe = pd.read_csv(path)
    fees = -stripe['Fees'].sum().round(2)
    deposit = stripe['Net'].sum().round(2)

    return fees, deposit


def reconcile(stripe_path: str, c7_path: str, debug=False):
    stripe_fees, stripe_deposit = read_stripe(stripe_path)

    if c7_path.endswith('.xlsx'):
        df = pd.read_excel(c7_path, sheet_name='All Data')
    else:
        df = pd.read_csv(c7_path)

    product_df = process_products(df)
    taxes_df = process_taxes(df)

    if debug:
        print(taxes_df)
        print(product_df)

    # Calculate deposit amount, sanity check
    deposit_amount = (
        product_df.Subtotal.sum() + taxes_df.Count.sum() + stripe_fees
    ).round(2)
    assert deposit_amount == stripe_deposit.round(2), (
        'Deposit total does not match Stripe Invoice'
    )

    # Generate the summary df
    blank_row = pd.DataFrame([[''] * 2], columns=['Count', 'Subtotal'], index=[''])
    deposit_row = pd.DataFrame(
        [[deposit_amount, '']], columns=['Count', 'Subtotal'], index=['Deposit Amount']
    )
    stripe_row = pd.DataFrame(
        [[stripe_fees, '']], columns=['Count', 'Subtotal'], index=['Stripe Fees']
    )
    product_row = pd.DataFrame(
        [['', '']], columns=['Count', 'Subtotal'], index=['Product']
    )
    summary = pd.concat(
        [
            product_row,
            product_df.set_index('Products'),
            blank_row,
            taxes_df,
            blank_row,
            stripe_row,
            blank_row,
            deposit_row,
        ],
        axis=0,
    )
    summary = summary.reset_index().fillna('')

    # Write the summary to csv in James' Format:

    if debug:
        print(summary)
    else:
        # Get date from stripe path
        date = '_'.join(stripe_path.split()[:2])
        print(date)

        try:
            pass
            # summary.to_csv(f'{date}.csv', index=False, header=False)
        except Exception as e:
            print(e)


if __name__ == '__main__':
    # Resolve CLI args
    args = parse_args()
    stripe_path = args.stripe
    commerce7 = args.commerce7
    debug = args.debug

    print(stripe_path, commerce7, debug)
