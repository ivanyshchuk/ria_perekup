from peewee import *
import datetime

db = SqliteDatabase('db.db')


class User(Model):
    class Meta:
        database = db

    chat_id = BigIntegerField(unique=True, index=True)
    username = CharField(null=True)
    is_active = BooleanField(default=True)
    history = TextField(null=True)
    search_url = TextField(null=True)
    modified = DateTimeField(default=datetime.datetime.now)
    created = DateTimeField(default=datetime.datetime.now)


db.connect()
db.create_tables([User])
