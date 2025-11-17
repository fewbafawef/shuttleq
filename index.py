from flask import Flask, render_template, request, redirect, url_for, session
import json
import time
import random
import secrets
import string

import firebase_admin
from firebase_admin import credentials, auth, db

print("logging in to the firebase")
try:
    cred = credentials.Certificate("serviceaccountkey.json")
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://shuttleq-jeffjeff9000-default-rtdb.asia-southeast1.firebasedatabase.app/'
    })
    print("logged in to the firebase 👍👍👍")
except FileNotFoundError:
    print("!!! FAILED TO LOGIN TO FIREBASE !!!")
    print("!!! serviceaccountkey.json not found. Please make sure it is in the same directory. !!!")
    exit(1)
except ValueError as e:
    print(f"Firebase already initialized? Error: {e}")
    pass


#app config stuff
app = Flask(__name__, static_url_path='/static', static_folder='./static', template_folder='./templates')
app.secret_key = "supersecretkey"
alphabet = string.ascii_letters + string.digits

SESSIONS_REF = db.reference('sessions')

#+++++++++++++++++++++++ HELPER STUFF +++++++++++++++++++++++++++++++

def parseRoomID(roomid_str):
    """
    Validates that the room ID is an 8-digit string.
    Returns the string if valid, None otherwise.
    """
    if not (roomid_str.isdigit() and len(roomid_str) == 8):
        return None
    return roomid_str

def generateErrorPage(title, msg):
    """Renders a custom error page."""
    return render_template("errormessage.html", error=title, message=msg), 400

def get_session_data(roomid_str):
    """Fetches session data from Firebase RTDB given a valid 8-digit string ID."""
    if not parseRoomID(roomid_str):
        return None
    
    try:
        session_ref = SESSIONS_REF.child(roomid_str)
        return session_ref.get()
    except Exception as e:
        print(f"Error fetching session data for {roomid_str}: {e}")
        return None

def is_session_valid(session_data):
    """Checks if session data exists and has not expired."""
    if not session_data:
        return False
    
    expiry_time = session_data.get('sessionexpiry', 0)
    if time.time() > expiry_time:
        print(f"Session expired.")
        return False
        
    return True

#++++++++++++++++++++++++ MAIN CODE +++++++++++++++++++++++++++++++

@app.route('/')
def landing():
    """Serves the home page."""
    return render_template("home.html", newlink=url_for("mknewsession"))

#main endpoitns
@app.route('/new')
def mknewsession():
    """Creates a new session in Firebase RTDB and redirects to the admin page."""
    password = ''.join(secrets.choice(alphabet) for i in range(8))
    uid_int = 0
    session_path = ""
    max_attempts = 10 
    
    for _ in range(max_attempts):
        uid_int = random.randint(0, 99999999)
        session_path = str(uid_int).zfill(8) 
        session_ref = SESSIONS_REF.child(session_path)
        if session_ref.get() is None:
            break 
        return generateErrorPage(
            "Room creation error", 
            "Could not find a unique room ID after multiple attempts."
        )

    session_data = {
        'adminpassword': password,
        'sessionexpiry': time.time() + 60*60, 
        'created_at': time.time()
    }

    try:
        SESSIONS_REF.child(session_path).set(session_data) 
        return redirect(url_for("roomadmin", roomid=session_path, passphrase=password))
        
    except Exception as e:
        print(f"Firebase write error: {e}")
        return generateErrorPage(
            "Room could not be created", 
            "A room could not be created for you, negative aura ---"
        )


#admin page
@app.route('/<roomid>/<passphrase>', methods=['GET', 'POST'])
def roomadmin(roomid, passphrase):
    """Admin page for a specific room, requires correct roomid and passphrase."""
    roomid_str = parseRoomID(roomid)
    if not roomid_str:
        return generateErrorPage("Invalid room id", "Room ID format is invalid. Must be 8 digits.")

    session_data = get_session_data(roomid_str)
    if not is_session_valid(session_data) or session_data.get('adminpassword') != passphrase:
        error_message = "We could not get your room. The ID might be wrong, the session may have expired, or the passphrase is incorrect."
        if request.method == 'POST':
            return {"message": "failed", "error": error_message}
        else:
            return generateErrorPage("Access Denied", error_message)
    if request.method == 'POST':
        return {"message": "success", "roomid": roomid_str}
    else:
        admin_url = url_for('roomadmin', roomid=roomid_str, passphrase=passphrase, _external=True)
        player_url = url_for('roombase', roomid=roomid_str, _external=True)
        display_url = url_for('roomdisplay', roomid=roomid_str, _external=True)
        return render_template("admin.html", 
                               admin_url=admin_url, 
                               player_url=player_url, 
                               display_url=display_url, 
                               roomid=roomid_str, 
                               passphrase=passphrase)

#players
@app.route('/<roomid>', methods=['GET','POST'])
def roombase(roomid):
    roomid_str = parseRoomID(roomid)
    if not roomid_str:
        return generateErrorPage("Invalid room id", "Room ID format is invalid. Must be 8 digits.")
    session_data = get_session_data(roomid_str)
    if not is_session_valid(session_data):
        error_message = "We could not get your room. The ID might be wrong or the session may have expired."
        if request.method == 'POST':
            return {"message": "failed", "error": error_message}
        return generateErrorPage("Could not get room", error_message)
    if request.method == 'POST':
        return {"message": "this is post success.", "roomid": roomid_str}
    return render_template("player.html", id=roomid_str)

#display
@app.route('/<roomid>/display')
def roomdisplay(roomid):
    roomid_str = parseRoomID(roomid)
    if not roomid_str:
        return generateErrorPage("Invalid Room ID Format", "The Room ID you provided is not a valid 8-digit number. Please check again.")
    session_data = get_session_data(roomid_str)
    if not is_session_valid(session_data):
        return generateErrorPage("Room Not Found", "We couldn't find a session for that ID. Please check that you entered the 8-digit Room ID correctly, or that the session hasn't expired.")
    return render_template("display.html", id=roomid_str)

if __name__ == '__main__':
    app.run(debug=True)