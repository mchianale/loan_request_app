import streamlit as st
import asyncio
from cookies_controller import get_persistent_controller, MAX_AGE
from client import login, register, retrieve_user_information, retrieve_user_loans, BASE_URL
from loanObjects import UserInformation, get_values_marital_status, get_work_status_values

from notifier_ws import NotifierThread, get_ws_connection
from streamlit.runtime.scriptrunner import add_script_run_ctx, get_script_run_ctx


#from streamlit_push_notifications import send_push

controller = get_persistent_controller()

# Hide the streamlit upper-right chrome
st.html(
    """
    <style>
    [data-testid="stStatusWidget"] {
            visibility: hidden;
            height: 0%;
            position: fixed;
        }
    </style>
    """,
)
if st.get_option("client.toolbarMode") != "minimal":
    st.set_option("client.toolbarMode", "minimal")
    st.rerun()


if "userInformation" not in st.session_state:
    st.session_state.userInformation = None
if "userLoans" not in st.session_state:
    st.session_state.userLoans = None

if "credit_page" not in st.session_state:
    st.session_state.credit_page = "login"
if "pending_notifications" not in st.session_state:
    st.session_state.pending_notifications = []


def _login():
    with st.form(key='login', clear_on_submit=False):
        st.subheader(':green[Log in]')
        username = st.text_input(':blue[Username]', placeholder='Enter Your Username')
        password = st.text_input(':blue[Password]', placeholder='Enter Your Password', type='password')

        submitted = st.form_submit_button("Log In")
        if submitted:
            response = asyncio.run(login(username=username, password=password, url=f"{BASE_URL}/login"))
            if response.status_code == 201:
                access_token = response.json()['token']['access_token']
                controller.set('access_token', access_token, max_age=MAX_AGE)
                #st.balloons()
                st.rerun()
            else:
                error_msg = response.json().get('detail')
                error_msg = error_msg[0].get('msg') if isinstance(error_msg, list) else error_msg
                st.warning(error_msg)

    if st.button('Sign up'):
        st.session_state.credit_page = "signup"
        st.rerun()
        

def _signup():
    with st.form(key='signup', clear_on_submit=False):
        st.subheader(':green[Sign up]')
        # Credentials
        username = st.text_input(':blue[Username]', placeholder='Enter Your Username')
        password1 = st.text_input(':blue[Password]', placeholder='Enter Your Password', type='password')
        password2 = st.text_input(':blue[Confirm Password]', placeholder='Confirm Your Password', type='password')
        
        # Personal Data fields
        last_name = st.text_input(':blue[Last Name]', placeholder='Enter Your Last Name')
        first_name = st.text_input(':blue[First Name]', placeholder='Enter Your First Name')
        email = st.text_input(':blue[Email]', placeholder='Enter Your Email')
        phone = st.text_input(':blue[Phone]', placeholder='Enter Your Phone Number')
        address = st.text_input(':blue[Address]', placeholder='Enter Your Address')

        date_of_birth = st.date_input(':blue[Date of Birth]',  format='YYYY-MM-DD')   
        marital_status = st.selectbox(':blue[Marital Status]', placeholder='Enter Your Marital Status', options=tuple(get_values_marital_status())) #, value=st.session_state.userInformation.marital_status.value)
        number_of_dependents = st.number_input(':blue[Number of Dependents]', min_value=0, step=1, value=0)

        nationality = st.text_input(':blue[Nationality]', placeholder='Enter Your Nationality')
        tax_residence = st.text_input(':blue[Tax Residence]', placeholder='Enter Your Tax Residence')

        work_status = st.selectbox(':blue[Work Status]', placeholder='Enter Your Work Status', options=tuple(get_work_status_values()))  
        gross_monthly_income = st.number_input(':blue[Gross Monthly Income]', min_value=0.0, step=0.1, value=0.0)    
        
        submitted = st.form_submit_button("Sign Up")
        if submitted:
            if password1 != password2:
                st.warning('Passwords Do Not Match')
            else:
                response = asyncio.run(
                    register(
                        username=username,
                        password=password1,
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
                        url=f"{BASE_URL}/register"
                    )
                )
                if response.status_code == 201:
                    access_token = response.json()['token']['access_token']
                    controller.set('access_token', access_token, max_age=MAX_AGE)
                    st.rerun()
                else:
                    error_msg = response.json().get('detail')
                    error_msg = error_msg[0].get('msg') if isinstance(error_msg, list) else error_msg
                    st.warning(error_msg)

    if st.button('Log in'):
        st.session_state.credit_page = "login"
        st.rerun()

def _logout():
    st.session_state.ws.close()
    st.session_state.clear() 
    controller.remove('access_token')
    st.rerun()


# define all pages
logout_page = st.Page(_logout, title="Log out", icon=":material/logout:")
settings = st.Page("settings.py", title="Settings", icon=":material/settings:")
credit_history = st.Page("credit_history.py", title="Credit History", icon=":material/credit_card:")
add_creddit = st.Page("add_credits.py", title="Add a Credit", icon=":material/credit_card:")
create_loan = st.Page("create_loan_request.py", title="New Loan Request", icon=":material/credit_card:")
all_loans = st.Page("dashboard.py", title="Your loans", icon=":material/credit_card:")
# Account pages
account_pages = [settings, logout_page]
creddit_pages = [credit_history, add_creddit]
loan_pages = [all_loans, create_loan]

if 'access_token' in controller.getAll():

    if st.session_state.userInformation is None:
        response = asyncio.run(retrieve_user_information(access_token=controller.get("access_token"), url=f"{BASE_URL}/retrieve_user_information"))
        if response.status_code == 200:
            response = response.json()
            del response['message']
            st.session_state.userInformation = UserInformation(**response)           
        else:
            st.rerun()

        if "say_hello" not in controller.getAll():
            st.toast(f"👋 Welcome home {st.session_state.userInformation.username}")
            # start ws listener
    if st.session_state.userLoans is None:
        response =  asyncio.run(retrieve_user_loans(access_token=controller.get("access_token"), url=f"{BASE_URL}/retrieve_user_loans"))
        if response.status_code == 200:
            response = response.json()
            st.session_state.userLoans = response.get("loans")  # list 
            st.session_state.userLoans = list(reversed(st.session_state.userLoans))
        else:
            st.rerun()
        
    if "ws" not in st.session_state:
        st.session_state.ws = get_ws_connection(controller.get('access_token'))
        thread = NotifierThread(st.session_state.ws)
        add_script_run_ctx(thread, get_script_run_ctx())
        thread.start()
            
    pg = st.navigation(
        {
            "Account": account_pages,
            "Credits history": creddit_pages,
            "Manage Loans" : loan_pages,      
        }
    )

    
else:
    if st.session_state.credit_page == "login":
        pg = st.navigation([st.Page(_login)])
    elif st.session_state.credit_page == "signup":
        pg = st.navigation([st.Page(_signup)])
    
pg.run()
