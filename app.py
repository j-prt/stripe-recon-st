import io

import pandas as pd
import streamlit as st

import stripe_recon as sr
from cleaner import clean_c7
from generate_url import generate

# Setup for reloading
if 'uploader_version' not in st.session_state:
    st.session_state.uploader_version = 0

st.session_state.error = False


def reset():
    for key in ('stripe', 'c7'):
        if key in st.session_state:
            del st.session_state[key]
    st.session_state.uploader_version += 1
    st.rerun()


st.title('Stripe Reconciliation')

st.header('Step 1: Upload Stripe File (csv)')
stripe_key = f'stripe_{st.session_state.uploader_version}'
stripe_file = st.file_uploader('Upload Stripe File', type=['csv'], key=stripe_key)

if stripe_file is not None:
    stripe_file = io.TextIOWrapper(stripe_file, encoding='utf-8')
    url = generate(stripe_file)
    st.subheader('')
    st.write(url)

    st.header('Step 2: Upload C7 Details (csv)')
    c7_key = f'c7_{st.session_state.uploader_version}'
    commerce7 = st.file_uploader('Upload C7 Details', type=['csv'], key=c7_key)

    if commerce7 is not None:
        stripe_file.seek(0)
        stripe, fees, deposit = sr.read_stripe(stripe_file)

        # Not using the original read_c7 func because commerce7
        # is not a filepath but a file-like obj
        c7 = pd.read_csv(commerce7)
        c7 = clean_c7(stripe, c7)

        # DEBUG
        # print('✌️✌️✌️✌️✌️✌️✌️✌️✌️✌️✌️✌️✌️✌️✌️')
        # print(
        #     'c7 len:',
        #     len(c7[~c7.duplicated('Order Number')]),
        #     'stripe len:',
        #     len(stripe),
        # )
        try:
            results = sr.reconcile(fees, deposit, c7, True, True)
        except Exception:
            st.session_state.error = True
            st.write(
                'Error: Commerce7 file cannot be reconciled with Stripe file. \n'
                'Check that the correct date range was used, and order details were exported.'
            )
            if st.button('Try Again'):
                reset()

        if not st.session_state.error:
            st.subheader('Download Summary CSV')
            csv_bytes = (
                results['summary'].to_csv(index=False, header=False).encode('utf-8')
            )
            st.download_button(
                label='Download Summary CSV',
                data=csv_bytes,
                file_name='output.csv',
                mime='text/csv',
            )

            st.subheader('Download Complete Excel Workbook')
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                c7.to_excel(writer, sheet_name='All Data', index=False)
                results['products'].to_excel(writer, sheet_name='Products', index=False)
                results['taxes'].to_excel(writer, sheet_name='Taxes', index=True)
                results['summary'].to_excel(
                    writer, sheet_name='Summary', index=False, header=False
                )
            output.seek(0)
            st.download_button(
                label='Download Complete Excel workbook',
                data=output,
                file_name='output.xlsx',
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            )

            if st.button('Start Over 🔄'):
                reset()
