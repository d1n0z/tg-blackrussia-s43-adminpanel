from peewee import SqliteDatabase, Model, TextField, BigIntegerField, IntegerField

from config import DATABASE

dbhandle = SqliteDatabase(DATABASE)


class Users(Model):
    nickname = TextField()
    role = TextField(null=True)
    fraction = TextField(null=True)
    appointed = BigIntegerField()
    promoted = BigIntegerField(null=True)
    objective_completed = BigIntegerField(null=True, default=0)
    apa = BigIntegerField(default=0)
    rebuke = BigIntegerField(default=0)
    warn = BigIntegerField(default=0)
    verbal = BigIntegerField(default=0)
    inactivestart = BigIntegerField(null=True)
    inactiveend = BigIntegerField(null=True)
    name = TextField()
    age = BigIntegerField()
    city = TextField()
    discord_id = BigIntegerField()
    telegram_id = BigIntegerField()
    forum = TextField()
    vk = TextField()
    coins = IntegerField(default=0)
    coins_last_spend = BigIntegerField(default=0)

    class Meta:
        database = dbhandle
        table_name = "users"


class Fractions(Model):
    name = TextField()
    nickname = TextField()
    trust9 = TextField()
    online = BigIntegerField()
    workers = BigIntegerField()
    lastupdate = BigIntegerField()

    class Meta:
        database = dbhandle
        table_name = "fractions"


class Removed(Model):
    nickname = TextField()
    role = TextField(null=True)
    fraction = TextField(null=True)
    appointed = BigIntegerField()
    name = TextField()
    age = BigIntegerField()
    city = TextField()
    discord_id = BigIntegerField()
    telegram_id = BigIntegerField()
    forum = TextField()
    vk = TextField()
    whoremoved = TextField()
    reason = TextField(null=True)
    date = TextField()
    struct = TextField()

    class Meta:
        database = dbhandle
        table_name = "removed"


class Inactives(Model):
    nickname = TextField()
    role = TextField(null=True)
    fraction = TextField(null=True)
    start = TextField()
    end = TextField()
    status = TextField()
    reason = TextField(null=True)

    class Meta:
        database = dbhandle
        table_name = "inactives"


class Chats(Model):
    setting = TextField()
    chat_id = BigIntegerField()
    thread_id = BigIntegerField(null=True)

    class Meta:
        database = dbhandle
        table_name = "chats"


class Sheets(Model):
    setting = TextField()
    val = TextField()

    class Meta:
        database = dbhandle
        table_name = "sheets"


class Settings_s(Model):  # noqa
    setting = TextField()
    val = BigIntegerField()

    class Meta:
        database = dbhandle
        table_name = "settingss"


class Settings_l(Model):  # noqa
    setting = TextField()
    val = BigIntegerField()

    class Meta:
        database = dbhandle
        table_name = "settingsl"


class Settings_a(Model):  # noqa
    setting = TextField()
    val = BigIntegerField()

    class Meta:
        database = dbhandle
        table_name = "settingsa"


class Forms(Model):
    form = TextField()
    proofs = TextField(null=True)
    fromtgid = BigIntegerField()

    class Meta:
        database = dbhandle
        table_name = "forms"


class InactiveRequests(Model):
    tgid = TextField()
    reason = TextField()
    start = TextField()
    end = TextField()
    w = BigIntegerField()

    class Meta:
        database = dbhandle
        table_name = "inactiverequests"


class SpecialAccesses(Model):
    telegram_id = TextField()
    role = TextField()

    class Meta:
        database = dbhandle
        table_name = "specialaccess"


class Objectives(Model):
    telegram_id = TextField()
    time = BigIntegerField()

    class Meta:
        database = dbhandle
        table_name = "objectives"


class CoinsLog(Model):
    telegram_id = TextField()
    lot_name = TextField()
    date = BigIntegerField()

    class Meta:
        database = dbhandle
        table_name = "coinslog"


class CoinsRequests(Model):
    telegram_id = TextField()
    lot_name = TextField()

    class Meta:
        database = dbhandle
        table_name = "coinsrequests"
