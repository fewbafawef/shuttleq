from flask import Flask, render_template, request, redirect, url_for, session
from flask_session import Session
import json
import time
import random
import secrets
import string
from models import PlaySession, db

#app config stuff
app = Flask(__name__, static_url_path='/static', static_folder='./static', template_folder='./templates')
app.secret_key = "supersecretkey"
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_PERMANENT"] = True
Session(app)
alphabet = string.ascii_letters + string.digits

#database 
db.connect()
db.create_tables([PlaySession])

#In-memory set of active UIDs this helps to check if the randomly generated thing exists.
active_sessions = list()
for s in PlaySession.select():
    if s.sessionexpiry > time.time():
        active_sessions.append(s.uid)

#generic home page
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
        return render_template("errormessage.html", error="Room could not be created", message="A room could not be created for you, negative aura ---")

@app.route('/<roomid>', methods=['GET','POST'])
def roombase(roomid):
    if not (roomid.isdigit() and len(roomid)==8):
        return "invalid room id"
    roomid = int(roomid)

    playsession = PlaySession.get_or_none(PlaySession.uid == roomid)

    if not playsession:
        if request.method == 'POST':
            return 'post faield caued room no there'
        return render_template("errormessage.html", error="Could not get room", message="We could not get your room, maybe cause the id is wrong.")

    if request.method == 'POST':
        return 'this is post success.'
            
    return render_template("player.html", id=roomid)

@app.route('/<roomid>/<passphrase>', methods=['GET', 'POST'])
def roomadmin(roomid, passphrase):
    if not (roomid.isdigit() and len(roomid)==8):
        return "invalid room id"
    roomid = int(roomid)

    playsession = PlaySession.get_or_none((PlaySession.uid == roomid) & (PlaySession.adminpassword == passphrase))

    if not playsession:
        if request.method == 'POST':
            return 'post faield caued room no there or password wrong'
        return render_template("errormessage.html", error="Could not get room", message="we could not get your room, maybe the id is wrong.")

    if request.method == 'POST':
        return 'this is post success.'

    return render_template("admin.html", id=roomid, passe=passphrase)


@app.route('/<roomid>/display')
def roomdisplay(roomid):
    if not (roomid.isdigit() and len(roomid)==8):
        return "invalid room id"
    roomid = int(roomid)

    playsession = PlaySession.get_or_none(PlaySession.uid == roomid)

    if not playsession:
        return render_template("errormessage.html", error="couldnt get room", message="the room could not be found, is the id right?")

    return render_template("display.html", id=roomid)

if __name__ == '__main__':
    app.run(debug=True)