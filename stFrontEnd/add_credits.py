import streamlit as st
import asyncio 
import pandas as pd

from cookies_controller import get_persistent_controller
from client import update_credits_history, BASE_URL
from loanObjects import get_values_credit_type, get_values_credit_status, get_values_payment_status


controller = get_persistent_controller()
# retrieve informations 
if "userInformation" not in st.session_state or st.session_state.userInformation is None or 'access_token' not in controller.getAll():
    st.rerun()

if "current_payment_history" not in st.session_state:
    st.session_state.current_payment_history = []

if "visualCredits" not in st.session_state:
    st.session_state.visualCredits = [
            {
                "credit type" : credit['credit_type'],
                "start date" : credit['start_date'],
                "amount" : credit['amount'],
                "duration months" : credit['duration_months'],
                "annual rate" : credit['annual_rate'],
                "status" : credit['status'],
                "selected" : False
            }
            for credit in st.session_state.userInformation.credits
    ]

st.header("💳 Add a Credit to your credit's history")
st.subheader(':green[New Credit]')

# One credit fields
credit_type = st.selectbox(':blue[Credit Type]', placeholder='Enter Your Credit Type', options=tuple(get_values_credit_type()))
start_date = st.date_input(':blue[Start Date]',  format='YYYY-MM-DD')
amount = st.number_input(':blue[Amount]', min_value=0.0, step=1.0, value=0.0, format="%.2f")
duration_months = st.number_input(':blue[Duration in Months]', min_value=1, step=1, value=1)
annual_rate = st.number_input(':blue[Annual Rate in %]', min_value=0.0, step=1.0, value=0.0, format="%.2f")
status = st.selectbox(':blue[Status]', placeholder='Enter Your Status', options=tuple(get_values_credit_status()))

st.subheader(':blue[- add a payment to this new credit]')
payment_date = st.date_input(':blue[Payment Date]',  format='YYYY-MM-DD')
payment_status = st.selectbox(':blue[Payment Status]', placeholder='Enter the payment status', options=tuple(get_values_payment_status()))
add_payment = st.button(":blue[Add this payment]")
if add_payment:
    st.session_state.current_payment_history.append({
        'payment_date': str(payment_date),
        'status': payment_status
    })

if st.session_state.current_payment_history:
    df_payment_history = pd.DataFrame(
        st.session_state.current_payment_history
    )
    st.table(df_payment_history)

add_new_credit = st.button(":green[Add the new credit]")
if add_new_credit:
    new_credit = {
        "credit_type": credit_type,
        "start_date": str(start_date),
        "amount": amount,
        "duration_months": duration_months,
        "annual_rate": annual_rate,
        "status": status,
        "payment_history": st.session_state.current_payment_history
    }
           
    response = asyncio.run(
    update_credits_history(
            access_token=controller.get("access_token"),
            credits= [new_credit] + st.session_state.userInformation.credits,
            url=f"{BASE_URL}/update_credits_history"
        )
    )
    if response.status_code == 200:
        st.session_state.current_payment_history = []
        st.session_state.userInformation.credits.append(new_credit)
        st.session_state.visualCredits.append( {
                "credit type" : new_credit['credit_type'],
                "start date" : new_credit['start_date'],
                "amount" : new_credit['amount'],
                "duration months" : new_credit['duration_months'],
                "annual rate" : new_credit['annual_rate'],
                "status" : new_credit['status'],
                "selected" : False
            })
        st.success(response.json().get("message"))
    else:
        error_msg = response.json().get('detail')
        error_msg = error_msg[0].get('msg') if isinstance(error_msg, list) else error_msg
        st.warning(error_msg)