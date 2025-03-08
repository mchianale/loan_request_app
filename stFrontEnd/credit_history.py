import streamlit as st
import asyncio 
import pandas as pd

from cookies_controller import get_persistent_controller
from client import update_credits_history , BASE_URL


controller = get_persistent_controller()
# retrieve informations 
if "userInformation" not in st.session_state or st.session_state.userInformation is None or 'access_token' not in controller.getAll():
    st.rerun()

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


st.header("💳 Credit History")
st.subheader(':green[Manage your credit history]')
df_credits = pd.DataFrame(
    st.session_state.visualCredits
)
edited_df_credits = st.data_editor(df_credits, width=1000)
if df_credits.shape[0] > 0:
    selected_credits = edited_df_credits.loc[edited_df_credits["selected"]].index.to_list()
    if selected_credits:
        delete_credits_btn = st.button(":red[Delete selected credits]")
        if delete_credits_btn:
            delete_credits = [st.session_state.userInformation.credits[i] for i in range(len(st.session_state.userInformation.credits)) if i not in selected_credits]
            response = asyncio.run(
            update_credits_history(
                    access_token=controller.get("access_token"),
                    credits= delete_credits,
                    url=f"{BASE_URL}/update_credits_history"
                )
            )
            if response.status_code == 200:
                st.session_state.userInformation.credits = delete_credits 
                st.session_state.visualCredits = [st.session_state.visualCredits[i] for i in range(len(st.session_state.visualCredits)) if i not in selected_credits]
                st.rerun()
            else:
                error_msg = response.json().get('detail')
                error_msg = error_msg[0].get('msg') if isinstance(error_msg, list) else error_msg
                st.warning(error_msg)
 