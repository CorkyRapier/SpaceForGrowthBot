import logging
import time

from connect import con, cur

class Subscribe:
    def add_sub(data):
        with con:
            result = cur.execute("INSERT INTO subscribe_annonce(sub_id, annonce_id, tg_id_user) VALUES(?, ?, ?)", data)
            return result