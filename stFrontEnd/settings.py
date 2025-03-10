import streamlit as st
import asyncio 

from cookies_controller import get_persistent_controller
from client import update_personal_data, BASE_URL
from loanObjects import get_values_marital_status, get_work_status_values


controller = get_persistent_controller()
# retrieve informations 
if "userInformation" not in st.session_state or st.session_state.userInformation is None or 'access_token' not in controller.getAll():
    st.rerun()

st.header("⚙️ Settings")
with st.form(key='update_profile', clear_on_submit=True):
    st.subheader(':green[Update your profile]')
    # Personal Data fields
    last_name = st.text_input(':blue[Last Name]', placeholder='Enter Your Last Name', value=st.session_state.userInformation.last_name)
    first_name = st.text_input(':blue[First Name]', placeholder='Enter Your First Name', value=st.session_state.userInformation.first_name)
    email = st.text_input(':blue[Email]', placeholder='Enter Your Email', value=st.session_state.userInformation.email)
    phone = st.text_input(':blue[Phone]', placeholder='Enter Your Phone Number', value=st.session_state.userInformation.phone)
    address = st.text_input(':blue[Address]', placeholder='Enter Your Address', value=st.session_state.userInformation.address)

    date_of_birth = st.date_input(':blue[Date of Birth]',  format='YYYY-MM-DD', value=st.session_state.userInformation.date_of_birth)
    marital_status = st.selectbox(':blue[Marital Status]', placeholder='Enter Your Marital Status', options=tuple([st.session_state.userInformation.marital_status.value] + [v for v in get_values_marital_status() if v != st.session_state.userInformation.marital_status.value])) #, value=st.session_state.userInformation.marital_status.value)
    number_of_dependents = st.number_input(':blue[Number of Dependents]', min_value=0, step=1, value=st.session_state.userInformation.number_of_dependents)

    tax_residence = st.text_input(':blue[Tax Residence]', placeholder='Enter Your Tax Residence', value=st.session_state.userInformation.tax_residence)
    nationality = st.text_input(':blue[Nationality]', placeholder='Enter Your Nationality', value=st.session_state.userInformation.nationality)
    
    work_status = st.selectbox(':blue[Work Status]', placeholder='Enter Your Work Status', options=tuple([st.session_state.userInformation.work_status.value] + [v for v in get_work_status_values() if v != st.session_state.userInformation.work_status.value]))
    gross_monthly_income = st.number_input(':blue[Gross Monthly Income]', min_value=0.0, step=0.1, value=st.session_state.userInformation.gross_monthly_income)    
         
    submitted = st.form_submit_button("Update your profile")
    if submitted:
        response = asyncio.run(
            update_personal_data(
                access_token=controller.get("access_token"),
                last_name=last_name,
                first_name=first_name,
                date_of_birth=str(date_of_birth),
                address=address,
                marital_status=marital_status,
                number_of_dependents=int(number_of_dependents),
                tax_residence=tax_residence,
                nationality=nationality,
                email=email,
                phone=phone,
                work_status=work_status,
                gross_monthly_income=gross_monthly_income,
                url=f"{BASE_URL}/update_personal_data"
            )
        )
        if response.status_code == 200:
            st.success(response.json().get("message"))
        else:
            error_msg = response.json().get('detail')
            error_msg = error_msg[0].get('msg') if isinstance(error_msg, list) else error_msg
            st.warning(error_msg)