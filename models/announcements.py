import logging
import time

from connect import con, cur

class Annonce:
    def get_list():
        with con:
            result = cur.execute("SELECT * FROM annonce").fetchall()
            return result

    def check_double(data):
        with con:
            result = cur.execute("SELECT annonce_id FROM annonce WHERE tg_id_user = ? AND start_date = ? AND start_time = ?", data).fetchall()
            return result

    def delete(data):
        with con:
            result = cur.execute("DELETE FROM annonce WHERE annonce_id = ?", data)
            con.commit()

    def add(data):
        with con:
            result = cur.execute("""INSERT INTO 
                                        annonce(annonce_id, name, discription, start_date, start_time, tg_id_user) 
                                    VALUES(?, ?, ?, ?, ?, ?)""", data)
            con.commit()
            logging.info(f'{str(time.asctime())}: Add new annonce in database - user_id: "{data[5]}"')