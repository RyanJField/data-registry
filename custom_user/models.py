from django.contrib.auth.models import AbstractUser, AbstractBaseUser
import mysql.connector as mariadb

from .managers import CustomUserManager


#        pool_name='users_db_pool',
#        pool_size=3,


def _get_db_connection():
    connection = mariadb.connect(
        option_files='/home/ubuntu/.mysql/people.cnf',
        database='people'
    )
    return connection


class User(AbstractUser):

    objects = CustomUserManager()

    REQUIRED_FIELDS = []

    def full_name(self):
        conn = None
        try:
            conn = _get_db_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT full_name FROM user WHERE name = %s', (self.username,))
            row = cursor.fetchone()
            return row[0]
        except (ValueError, TypeError):
            return 'User Not Found'
        finally:
            if conn is not None: conn.close()

    def email(self):
        conn = None
        try:
            conn = _get_db_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT email FROM user WHERE name = %s', (self.username,))
            row = cursor.fetchone()
            return row[0]
        except (ValueError, TypeError):
            return 'User Not Found'
        finally:
            if conn is not None: conn.close()

    def orgs(self):
        sql = '''
        SELECT org.name FROM user, org, user_orgs 
        WHERE user.name = %s
          AND user_orgs.user_id = user.id
          AND user_orgs.org_id = org.id
        '''
        conn = None
        try:
            conn = _get_db_connection()
            cursor = conn.cursor()
            cursor.execute(sql, (self.username,))
            rows = cursor.fetchmany()
            return [row[0] for row in rows]
        except (ValueError, TypeError):
            return []
        finally:
            if conn is not None: conn.close()

    def clean(self):
        AbstractBaseUser.clean(self)

