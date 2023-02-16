import logging
import time

from connect import con, cur

class Users:
    def get_list():
        with con:
            result = cur.execute("SELECT * FROM users").fetchall()
            return result

    def new_user(data):
        with con:
            check = cur.execute("SELECT id_user FROM users WHERE tg_id_user = ?", (data[1],))
            if not len(check.fetchall()) > 0:
                result = cur.execute("INSERT INTO users(id_user, tg_id_user, full_name) VALUES(?, ?, ?)", data)
                con.commit()
                logging.info(f'{str(time.asctime())}: Add new user in database - user_id: "{data[1]}"')

    # def check_user(tg_id_user):
    #         result = cur.execute("SELECT id_user FROM users WHERE tg_id_user = ?", (tg_id_user,))
    #         print(len(result.fetchall()))
    #         return len(result.fetchall())
