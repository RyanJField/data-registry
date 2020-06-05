from django.contrib.auth.models import AbstractUser
import mysql.connector as mariadb


def _get_db_connection():
    connection = mariadb.connect(
        option_files='/home/ubuntu/.mysql/people.cnf',
        database='people'
    )
    return connection


class User(AbstractUser):

    def full_name(self):
        try:
            conn = _get_db_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT full_name FROM user WHERE name = %s', (self.username,))
            row = cursor.fetchone()
            return row[0]
        except ValueError:
            return 'User Not Found'

    def email(self):
        try:
            conn = _get_db_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT email FROM user WHERE name = %s', (self.username,))
            row = cursor.fetchone()
            return row[0]
        except ValueError:
            return 'User Not Found'

    def orgs(self):
        sql = '''
        SELECT org.name FROM user, org, user_orgs 
        WHERE user.name = %s
          AND user_orgs.user_id = user.id
          AND user_orgs.org_id = org.id
        '''
        try:
            conn = _get_db_connection()
            cursor = conn.cursor()
            cursor.execute(sql, (self.username,))
            rows = cursor.fetchmany()
            return [row[0] for row in rows]
        except ValueError:
            return []
