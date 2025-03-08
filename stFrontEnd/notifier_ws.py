 
import websocket
from threading import Thread
import streamlit as st
import json


def get_ws_connection(access_token : str):
    try:
        ws = websocket.create_connection(f"ws://localhost:8004/ws/{access_token}")
        return ws
    except websocket.WebSocketConnectionClosedException:
        raise "WebSocket connection already closed."
    except Exception as e:
        raise f"WebSocket error: {str(e)}"

class NotifierThread(Thread):
    def __init__(self, ws):
        super().__init__()
        self.ws = ws
       
    def run(self):
        if "notifications" not in st.session_state:
            st.session_state.notifications = []
        try:
            while True:
                result = self.ws.recv()
                st.session_state.notifications.append(json.loads(result))
                 
        except websocket.WebSocketConnectionClosedException:
            print("WebSocket connection already closed.")
        except Exception as e:
            print(f"WebSocket error: {str(e)}")
        finally:
            if self.ws:
                self.ws.close()  # Ensure the WebSocket is closed if an error occurs
                print("WebSocket connection closed.")
            
     

