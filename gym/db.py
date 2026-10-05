import os
from pathlib import Path
from dotenv import load_dotenv
import mysql.connector
from gym.service import Gym

load_dotenv(Path(__file__).resolve().parents[1] / '.env')

def connect():
    return mysql.connector.connect(host=os.getenv('MYSQL_HOST','127.0.0.1'), port=int(os.getenv('MYSQL_PORT','3306')), user=os.getenv('MYSQL_USER','gym_app'), password=os.environ['MYSQL_PASSWORD'], database=os.getenv('MYSQL_DATABASE','gym_manager'), connection_timeout=10)

gym = Gym(connect)
