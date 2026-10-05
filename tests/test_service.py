import sqlite3
import tempfile
import unittest
from pathlib import Path
from gym.service import Gym

class Cursor:
    def __init__(self, cur): self.cur=cur
    def execute(self, sql, args=()):
        self.cur.execute(sql.replace('%s','?').replace(' FOR UPDATE',''),args)
    @property
    def lastrowid(self): return self.cur.lastrowid
    def fetchall(self): return [dict(r) for r in self.cur.fetchall()]
    def fetchone(self):
        r=self.cur.fetchone()
        return dict(r) if r else None
class Connection:
    def __init__(self,path):
        self.conn=sqlite3.connect(path)
        self.conn.row_factory=sqlite3.Row
        self.conn.execute('PRAGMA foreign_keys=ON')
    def cursor(self,dictionary=True): return Cursor(self.conn.cursor())
    def commit(self): self.conn.commit()
    def rollback(self): self.conn.rollback()
    def close(self): self.conn.close()
class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.path=Path(self.tmp.name)/'test.db'
        conn=sqlite3.connect(self.path)
        conn.executescript('''
        CREATE TABLE members(id INTEGER PRIMARY KEY,name TEXT,phone TEXT UNIQUE);
        CREATE TABLE plans(id INTEGER PRIMARY KEY,name TEXT UNIQUE,duration_days INT,price NUMERIC);
        CREATE TABLE memberships(id INTEGER PRIMARY KEY,member_id INT REFERENCES members(id),plan_id INT REFERENCES plans(id),start_date TEXT,end_date TEXT,agreed_price NUMERIC);
        CREATE TABLE payments(id INTEGER PRIMARY KEY,membership_id INT REFERENCES memberships(id),amount NUMERIC,reference TEXT UNIQUE,recorded_at TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE attendance(id INTEGER PRIMARY KEY,member_id INT REFERENCES members(id),attended_on TEXT,UNIQUE(member_id,attended_on));
        ''')
        conn.close()
        self.gym=Gym(lambda:Connection(self.path))
    def tearDown(self): self.tmp.cleanup()
    def test_membership_and_payment(self):
        member=self.gym.add_member('Test Member','9000000000')['id']
        plan=self.gym.create_plan('Monthly',30,'1000.00')['id']
        membership=self.gym.activate_membership(member,plan,'2026-01-01')['id']
        self.assertEqual(self.gym.memberships(member)[0]['end_date'],'2026-01-30')
        payment=self.gym.record_payment(membership,'500.00','test-reference')
        self.assertFalse(payment['already_recorded'])
        self.assertTrue(self.gym.record_payment(membership,'500.00','test-reference')['already_recorded'])
        self.assertEqual(self.gym.memberships(member)[0]['paid'],500)
        with self.assertRaises(ValueError): self.gym.record_payment(membership,'600.00','test-reference')
        self.assertEqual(self.gym.search_members('Test')[0]['id'],member)
    def test_validation(self):
        for amount in ('-1','NaN','0','1.001'):
            with self.assertRaises(ValueError): self.gym.create_plan('Invalid',30,amount)
        with self.assertRaises(ValueError): self.gym.activate_membership(999,999,'2026-01-01')
        with self.assertRaises(ValueError): self.gym.expiring_memberships(-1)
    def test_attendance_dashboard_receipts_and_renewal(self):
        from datetime import date, timedelta
        member=self.gym.add_member('Alice','9000000001')['id']
        plan=self.gym.create_plan('Monthly',30,'1000')['id']
        with self.assertRaises(ValueError): self.gym.check_in(member)
        membership=self.gym.activate_membership(member,plan,date.today().isoformat())['id']
        visit=self.gym.check_in(member)
        self.assertFalse(visit['already_recorded'])
        self.assertTrue(self.gym.check_in(member)['already_recorded'])
        self.gym.record_payment(membership,'400','receipt-1')
        summary=self.gym.dashboard()
        self.assertEqual(summary['members'],1)
        self.assertEqual(summary['active_members'],1)
        self.assertEqual(summary['today_attendance'],1)
        self.assertEqual(summary['total_received'],400)
        self.assertEqual(summary['pending_balance'],600)
        self.assertEqual(self.gym.payment_history(member)[0]['reference'],'receipt-1')
        renewed=self.gym.renew_membership(member,plan)['id']
        rows=self.gym.memberships(member)
        self.assertEqual(next(r for r in rows if r['id']==renewed)['start_date'],(date.today()+timedelta(days=30)).isoformat())
        self.assertEqual({r['status'] for r in self.gym.membership_report()},{'Active','Upcoming'})
        self.assertEqual(len(self.gym.attendance_report(date.today().isoformat(),date.today().isoformat())),1)
        self.gym.update_member(member,'Alice Updated','9000000002')
        self.assertEqual(self.gym.search_members('Updated')[0]['phone'],'9000000002')
        with self.assertRaises(ValueError):self.gym.attendance_report('2026-10-02','2026-10-01')
        with self.assertRaises(ValueError):self.gym.update_member(999,'Missing','123')

    def test_expired_renewal_and_advance_payment(self):
        from datetime import date, timedelta
        member=self.gym.add_member('Bob','9000000003')['id']
        plan=self.gym.create_plan('Day',1,'100')['id']
        membership=self.gym.activate_membership(member,plan,(date.today()-timedelta(days=2)).isoformat())['id']
        with self.assertRaises(ValueError):self.gym.check_in(member)
        self.gym.record_payment(membership,'150','advance')
        self.assertEqual(self.gym.dashboard()['pending_balance'],0)
        self.assertEqual(self.gym.membership_report()[0]['status'],'Expired')
        renewed=self.gym.renew_membership(member,plan)['id']
        self.assertEqual(next(r for r in self.gym.memberships(member) if r['id']==renewed)['start_date'],date.today().isoformat())

if __name__=='__main__': unittest.main()
