from models import PlaySession, db
import time

db.connect()
while True:
    deleted = PlaySession.delete().where(PlaySession.sessionexpiry < time.time()).execute()
    print(f"{deleted} entries deleted")
    time.sleep(60*60)