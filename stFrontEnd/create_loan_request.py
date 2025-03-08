import streamlit as st
import asyncio 
import pandas as pd

from cookies_controller import get_persistent_controller
from client import create_loan_request, BASE_URL
from loanObjects import get_values_credit_type, get_values_property_type



controller = get_persistent_controller()

# retrieve informations 
if "userInformation" not in st.session_state or st.session_state.userInformation is None or 'access_token' not in controller.getAll():
    st.rerun()

st.header("💳 Create a New Loan Request")
st.subheader(':green[New Loan Request]')

# One credit fields
credit_type = st.selectbox(':blue[Credit Type]', placeholder='Enter Your Credit Type', options=tuple(get_values_credit_type()))
loan_amount = st.number_input(':blue[Amount]', min_value=0.0, step=1.0, value=20000.0, format="%.2f")
duration_months = st.number_input(':blue[Favorite Duration in Months]', min_value=1, step=1, value=12)
purpose = st.text_input(':blue[Purpose of the Loan]', value="jdjd")
property_location = st.text_input(':blue[Location of the property]', value="jdjd")
property_value = st.number_input(':blue[Approximate price of this property]', min_value=0.0, step=1.0, value=2000.0, format="%.2f")
property_type = st.selectbox(':blue[Status]', placeholder='Type of the property', options=tuple(get_values_property_type()))


add_new_loan = st.button(":green[Add the new loan]")
if add_new_loan :

    response = asyncio.run(
    create_loan_request(
            access_token=controller.get("access_token"),
            credit_type=credit_type,
            loan_amount=loan_amount,
            duration_months=duration_months,
            purpose=purpose,
            property_location=property_location,
            property_value=property_value,
            property_type=property_type,
            url=f"{BASE_URL}/create_loan_request"
        )
    )
    if response.status_code == 201:
        loan = response.json().get("loan")
        st.success(loan.get("loan_message"))
        st.success("A response will be given to you in a very short time.")
        st.session_state.pending_notifications.append(f':green[{loan.get("loan_message")}]')  
    else:
        error_msg = response.json().get('detail')
        error_msg = error_msg[0].get('msg') if isinstance(error_msg, list) else error_msg
        st.warning(error_msg)