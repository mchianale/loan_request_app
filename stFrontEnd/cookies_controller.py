from streamlit_cookies_controller import CookieController

# cookies
MAX_AGE = 1800 # 1800 secondes = 30 min
controller : CookieController = None

def get_persistent_controller():
    global controller
    if controller is None:
        controller = CookieController()
    return controller
