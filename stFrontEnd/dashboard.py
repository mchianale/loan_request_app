import streamlit as st
import pandas as pd
from cookies_controller import get_persistent_controller
import time

controller = get_persistent_controller()
# retrieve loans 
if "userLoans" not in st.session_state or st.session_state.userLoans is None or 'access_token' not in controller.getAll():
    st.rerun()

 
if "db_loans" not in st.session_state or st.session_state.db_loans is None:
    visualLoans = [
            {
                "credit type" : loan['credit_type'],
                "created" : loan['created_at'],
                "loan amount" : loan['loan_amount'],
                "duration months" : loan['duration_months'],
                "status" : loan['loan_status'],
                "message" : loan['loan_message'],
                "selected" : False
            }
            for loan in st.session_state.userLoans
    ]
    st.session_state.df_loans = df_loans = pd.DataFrame(
        visualLoans
        )
    

st.header("💳 Manage your loans")

edited_df_loans = st.data_editor(st.session_state.df_loans, width=50000, use_container_width=False)

if st.session_state.df_loans.shape[0] > 0:
    selected_loan = edited_df_loans.loc[edited_df_loans["selected"]].index.to_list()
    if len(selected_loan) == 1:
        selected_loan = selected_loan[-1]
        current_loan = st.session_state.userLoans[selected_loan]
        if current_loan['loan_status'] == "Approved":
               st.balloons()
        for key, value in current_loan.items():
        
                if isinstance(value, dict) and value is not None:
                        if key != "repaymentSchedule":
                                st.subheader(f':blue[- {key.replace("_", " ").title()}]')
                                primary_key = key.split('_')[0]
                                for k,v in value.items():
                                        if v is not None and k != 'duration_months':
                                                st.text_input(primary_key + ' ' + k.replace("_", " ").title(), str(v), disabled=True)
                        else:
                                st.subheader(f':green[- Repayment Schedule]') 
                                st.date_input("Start date", value["start_date"],  format='YYYY-MM-DD')
                                df_payment_dates = pd.DataFrame(
                                        value["repaymentEvent"]
                                )
                                st.table(df_payment_dates)
                                        
                elif value is not None and key not in ['user_id', '_id']:
                        st.text_input(key.replace("_", " ").title(), str(value), disabled=True)

    elif len(selected_loan) > 1:
        st.warning('Please select only one loan !')
                        

while True:
        i = 0
        while i < len(st.session_state.notifications):
                notification = st.session_state.notifications[i]  # Get the current notification
                
                # Add message to pending notifications
                if notification['loan_status'] == "Cancelled":
                       message = f":orange[{notification['message']}]"
                elif notification['loan_status'] == "Denied":
                       message = f":red[{notification['message']}]"
                else:
                        message = f":green[{notification['message']}]"
                       
                st.session_state.pending_notifications.append(message)

                if notification.get('finish'):  # Check if the notification is finished
                        st.session_state.userLoans = None
                        st.session_state.db_loans = None
                        del st.session_state.notifications[i]
                       
                        st.rerun()  # Ensure Streamlit refreshes after processing

                # Remove the processed notification
                del st.session_state.notifications[i]  # Directly remove it
               

                # Don't increment i, since list shrinks when deleting items
                  
        i = 0
        while i < len(st.session_state.pending_notifications):
                st.toast(st.session_state.pending_notifications[i])
                del st.session_state.pending_notifications[i]
        time.sleep(1)
