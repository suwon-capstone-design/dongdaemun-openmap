import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from sshtunnel import SSHTunnelForwarder
from dbutils.pooled_db import PooledDB
import pymysql
from dotenv import load_dotenv

load_dotenv()


class MySQLPoolClient:
    def __init__(self):
        self.ssh_tunnel = None
        self.pool = None
        self._setup_ssh_tunnel()
        self._setup_connection_pool()

    def _setup_ssh_tunnel(self):
        self.ssh_tunnel = SSHTunnelForwarder(
            (os.getenv("SSH_HOST"), int(os.getenv("SSH_PORT"))),
            ssh_username=os.getenv("SSH_USER"),
            ssh_password=os.getenv("SSH_PASSWORD"),
            remote_bind_address=(os.getenv("DB_HOST"), int(os.getenv("DB_PORT"))),
            local_bind_address=('127.0.0.1',)
        )
        self.ssh_tunnel.start()
        print(f"[🔐 SSH 터널링 활성화] 로컬 포트: {self.ssh_tunnel.local_bind_port}")

    def _setup_connection_pool(self):
        self.pool = PooledDB(
            creator=pymysql,
            maxconnections=5,
            host='127.0.0.1',
            port=self.ssh_tunnel.local_bind_port,
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME"),
            charset=os.getenv("DB_CHARSET", "utf8mb4"),
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=True,
            blocking=True
        )

    def get_connection(self):
        return self.pool.connection()

    def close(self):
        if self.ssh_tunnel:
            self.ssh_tunnel.stop()
            print("[🔒 SSH 터널 종료]")
