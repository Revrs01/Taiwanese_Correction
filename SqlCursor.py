import pymysql.cursors


class Cursor:
    def __init__(self):
        self.connection = pymysql.connect(host='localhost',
                                          user='correction',
                                          password='taiwanesecorrection',
                                          database='taiwanese_correction')
        # self.connection = pymysql.connect(host='localhost',
        #                                   user='root',
        #                                   password='88159',
        #                                   database='taiwanese_correction')
    def get_connection(self):
        return self.connection
