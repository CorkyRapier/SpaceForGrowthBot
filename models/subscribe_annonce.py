import logging
import uuid
import time

from connect import con, cur

class Subscribe:
    def add_sub(data):
        with con:
            annonce_on_cod = cur.execute("SELECT annonce_id FROM annonce WHERE cod_u = ?", [data[0]]).fetchall()
            check_sub = cur.execute("""SELECT sub_id FROM subscribe_annonce 
                                        WHERE annonce_id = ? AND tg_id_user = ?""", [annonce_on_cod[0][0], data[1]]).fetchall()
            if check_sub == []:
                data = [str(uuid.uuid4()), annonce_on_cod[0][0], data[1]]
                result = cur.execute("""INSERT INTO subscribe_annonce(sub_id, annonce_id, tg_id_user) 
                                    VALUES(?, ?, ?)""", data)
                con.commit()
                return True
            return False

    def delete_sub(data):
        with con:
            annonce_on_cod = cur.execute("SELECT annonce_id FROM annonce WHERE cod_u = ?", [data[0]]).fetchall()
            print(data)
            print(annonce_on_cod)
            sub_id = cur.execute("""SELECT sub_id FROM subscribe_annonce 
                                        WHERE annonce_id = ? AND tg_id_user = ?""", [annonce_on_cod[0][0], data[1]]).fetchall()
            if sub_id == []:
                sub_id = [(None,),]
            cur.execute('DELETE FROM subscribe_annonce WHERE sub_id = ?', sub_id[0])
            con.commit()

    def get_list_events(tg_id_user):
        with con:
            result = cur.execute("""SELECT sub.annonce_id FROM subscribe_annonce sub
                                    LEFT JOIN annonce ON sub.annonce_id = annonce.annonce_id
                                    WHERE sub.tg_id_user = ?""", (tg_id_user,)).fetchall()
            if result is None:
                return False
            return result

    # def get_soon_events():
    #     with con:
    #         events_list = cur.execute("""SELECT * FROM subscribe_annonce sub
    #                                     LEFT JOIN annonce ON sub.annonce_id = annonce.annonce_id
    #                                     WHERE annonce.""")

