import io

import pandas as pd
import streamlit as st

import stripe_recon as sr
from cleaner import clean_c7
from generate_url import generate

# Setup for reloading
if 'uploader_version' not in st.session_state:
    st.session_state.uploader_version = 0

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

        # TODO: remove after testing
        print(c7, stripe)
        print(len(c7['Order Number'].unique()), len(stripe))

        summary = sr.reconcile(fees, deposit, c7, False)

        st.subheader('Download Summary Output')
        csv_bytes = summary.to_csv(index=False, header=False).encode('utf-8')
        st.download_button(
            label='Download Summary CSV',
            data=csv_bytes,
            file_name='output.csv',
            mime='text/csv',
        )

        if st.button('Start Over 🔄'):
            for key in ('stripe', 'c7'):
                if key in st.session_state:
                    del st.session_state[key]
            st.session_state.uploader_version += 1
            st.rerun()
