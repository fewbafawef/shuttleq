from peewee import SqliteDatabase, Model, CharField, IntegerField, BigIntegerField, TextField

db = SqliteDatabase("shuttleq.db")

class BaseModel(Model):
    class Meta:
        database = db

class PlaySession(BaseModel):
    uid = IntegerField(unique=True)
    adminpassword = CharField()

    editaccesspassword = CharField(null=True)
    viewaccesspassword = CharField(null=True)

    displayname = TextField(null=True)
    sessionsettings = TextField(null=True)
    playersettings = TextField(null=True)
    displaysettings = TextField(null=True)

    gameinfo = TextField(null=True)

    sessionexpiry = BigIntegerField()
