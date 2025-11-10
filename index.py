from flask import Flask, render_template, request, redirect, url_for, session
import json
import time
import random
import secrets
import string
from models import PlaySession, db
from flask_socketio import SocketIO, ConnectionRefusedError, join_room, leave_room, current_user

#app config stuff
app = Flask(__name__, static_url_path='/static', static_folder='./static', template_folder='./templates')
app.secret_key = "supersecretkey"
socketio = SocketIO(app)
alphabet = string.ascii_letters + string.digits

#database 
db.connect()
db.create_tables([PlaySession])
active_sessions = list()
for s in PlaySession.select():
    if s.sessionexpiry > time.time():
        active_sessions.append(s.uid)

#+++++++++++++++++++++++ HELPER STUFF +++++++++++++++++++++++++++++++

def parseRoomID(roomid):
    if not (roomid.isdigit() and len(roomid)==8):
        return None
    return int(roomid)

def generateErrorPage(title, msg):
    return render_template("errormessage.html", error=title, message=msg), 400

def getRoom(**kwargs):
    return PlaySession.get_or_none(**kwargs)


#++++++++++++++++++++++++ MAIN CODE +++++++++++++++++++++++++++++++

@app.route('/')
def landing():
    return render_template("home.html", newlink=url_for("mknewsession"))

#main endpoitns
@app.route('/new')
def mknewsession():
    uid = 0
    password = ''.join(secrets.choice(alphabet) for i in range(8))
    while True:
        uid = random.randint(0, 99999999)
        if uid not in active_sessions:
            break
    try:
        PlaySession.create(uid=uid, adminpassword=password, sessionexpiry=time.time()+60*60)
        active_sessions.append(uid)
        return redirect(url_for("roomadmin", roomid=str(uid).zfill(8), passphrase=password))
    except:
        return generateErrorPage("Room could not be created", "A room could not be created for you, negative aura ---")


#admin page
@app.route('/<roomid>/<passphrase>', methods=['GET', 'POST'])
def roomadmin(roomid, passphrase):
    roomid = parseRoomID(roomid)
    if not roomid:
        return generateErrorPage("invalid room id", "room id is invalid")

    if not getRoom(uid=roomid, adminpassword=passphrase):
        if request.method == 'POST':
            return {"message": "failed"}
        else:
            return generateErrorPage("Could not get room", "we could not get your room, maybe the id is wrong.")

    if request.method == 'POST':
        return {"message": "success"}
    else:
        roomid=str(roomid).zfill(8)
        admin_url = url_for('roomadmin', roomid=roomid, passphrase=passphrase, _external=True)
        player_url = url_for('roombase', roomid=roomid, _external=True)
        display_url = url_for('roomdisplay', roomid=roomid, _external=True)
        return render_template("admin.html", admin_url=admin_url, player_url=player_url, display_url=display_url, roomid=roomid, passphrase=passphrase)

#players
@app.route('/<roomid>', methods=['GET','POST'])
def roombase(roomid):
    roomid = parseRoomID(roomid)
    if not roomid:
        return generateErrorPage("invalid room id", "room id is invalid")

    if not getRoom(uid=roomid):
        if request.method == 'POST':
            return 'post faield caued room no there'
        return generateErrorPage("Could not get room", "We could not get your room, maybe cause the id is wrong.")

    if request.method == 'POST':
        return 'this is post success.'
            
    return render_template("player.html", id=roomid)

#display
@app.route('/<roomid>/display')
def roomdisplay(roomid):
    roomid = parseRoomID(roomid)
    if not roomid:
        return generateErrorPage("Invalid Room ID Format", "The Room ID you provided is not a valid 8-digit number. Please check again.")

    if not getRoom(uid=roomid):
        return generateErrorPage("Room Not Found", "We couldn't find a session for that ID. Please check that you entered the 8-digit Room ID correctly, or that the session hasn't expired.")

    return render_template("display.html", id=roomid)

#++++++++++++++++++++++++++++++ SOCKETS FOR REAL TIME THINGY +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

@socketio.on('connect')
def on_connect(auth):
    print(auth)
    if auth and "authpass" in auth and "room" in auth and "type" in auth:

        roomid = parseRoomID(auth['room'])

        if not roomid:
            raise ConnectionRefusedError("unauthorized!")

        print(auth['authpass'], roomid, auth['type'])
    else:
        raise ConnectionRefusedError("unauthorized!")

@socketio.on('connect')
def on_connect(auth):
    print(auth)
    if auth and "authpass" in auth and "room" in auth and "type" in auth:
        roomid = parseRoomID(auth['room'])
        if not roomid:
            raise ConnectionRefusedError("unauthorized!")
        join_room(roomid) 
        current_user.data['role'] = auth['type'] 
        current_user.data['room_id'] = roomid
        print(f"User connected! Role: {current_user.data['role']}, Room: {current_user.data['room_id']}")
        
    else:
        raise ConnectionRefusedError("unauthorized!")

if __name__ == '__main__':
    socketio.run(app, debug=True)
