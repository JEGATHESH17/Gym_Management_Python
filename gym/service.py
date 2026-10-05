from datetime import date, timedelta
from decimal import Decimal, InvalidOperation

class Gym:
    def __init__(self, connect):
        self.connect = connect

    def query(self, sql, args=(), write=False):
        conn = self.connect()
        try:
            cur = conn.cursor(dictionary=True)
            cur.execute(sql, args)
            result = {'id': cur.lastrowid} if write else cur.fetchall()
            if write:
                conn.commit()
            return result
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def add_member(self, name: str, phone: str):
        name, phone = name.strip(), phone.strip()
        if not name or not phone or len(name) > 100 or len(phone) > 30:
            raise ValueError('Provide a name (1–100 characters) and phone (1–30 characters).')
        return self.query('INSERT INTO members (name, phone) VALUES (%s,%s)', (name, phone), True)

    def search_members(self, query: str = ''):
        if len(query) > 100:
            raise ValueError('Search is limited to 100 characters.')
        return self.query('SELECT id,name,phone FROM members WHERE name LIKE %s OR phone LIKE %s ORDER BY id DESC LIMIT 100', (f'%{query}%', f'%{query}%'))

    def create_plan(self, name: str, duration_days: int, price: str):
        try:
            amount = Decimal(price)
        except InvalidOperation:
            raise ValueError('Price must be a decimal amount.')
        if not name.strip() or len(name) > 100 or not 1 <= duration_days <= 3650 or not amount.is_finite() or amount <= 0 or amount > Decimal('99999999.99') or amount != amount.quantize(Decimal('.01')):
            raise ValueError('Use a name, 1–3650 days, and a positive price with up to two decimals.')
        return self.query('INSERT INTO plans (name,duration_days,price) VALUES (%s,%s,%s)', (name.strip(),duration_days,str(amount)), True)

    def list_plans(self):
        return self.query('SELECT * FROM plans ORDER BY id')

    def activate_membership(self, member_id: int, plan_id: int, start_date: str):
        start = date.fromisoformat(start_date)
        plans = self.query('SELECT * FROM plans WHERE id=%s', (plan_id,))
        if not plans or not self.query('SELECT id FROM members WHERE id=%s', (member_id,)):
            raise ValueError('Member or plan does not exist.')
        plan = plans[0]
        end = start + timedelta(days=plan['duration_days']-1)
        return self.query('INSERT INTO memberships (member_id,plan_id,start_date,end_date,agreed_price) VALUES (%s,%s,%s,%s,%s)', (member_id,plan_id,start.isoformat(),end.isoformat(),str(plan['price'])), True)

    def record_payment(self, membership_id: int, amount: str, reference: str):
        try:
            value = Decimal(amount)
        except InvalidOperation:
            raise ValueError('Amount must be a decimal.')
        if not value.is_finite() or value <= 0 or value > Decimal('99999999.99') or value != value.quantize(Decimal('.01')) or not reference.strip() or len(reference) > 100:
            raise ValueError('Use a positive amount with up to two decimals and a unique reference (1–100 characters).')
        # Unique reference prevents accidental duplicate recordings, including concurrent requests.
        conn = self.connect()
        try:
            cur = conn.cursor(dictionary=True)
            cur.execute('SELECT id FROM memberships WHERE id=%s FOR UPDATE', (membership_id,))
            if not cur.fetchone():
                raise ValueError('Membership does not exist.')
            cur.execute('SELECT id,membership_id,amount FROM payments WHERE reference=%s', (reference.strip(),))
            existing = cur.fetchone()
            if existing:
                if existing['membership_id'] != membership_id or Decimal(str(existing['amount'])) != value:
                    raise ValueError('Reference already belongs to a different payment.')
                return {'id': existing['id'], 'already_recorded': True}
            cur.execute('INSERT INTO payments (membership_id,amount,reference) VALUES (%s,%s,%s)', (membership_id,str(value),reference.strip()))
            result = {'id': cur.lastrowid, 'already_recorded': False}
            conn.commit()
            return result
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def memberships(self, member_id: int):
        return self.query('SELECT s.*,p.name AS plan_name,COALESCE((SELECT SUM(amount) FROM payments WHERE membership_id=s.id),0) AS paid FROM memberships s JOIN plans p ON p.id=s.plan_id WHERE s.member_id=%s ORDER BY s.end_date DESC', (member_id,))

    def expiring_memberships(self, days: int = 7):
        if not 0 <= days <= 365:
            raise ValueError('Days must be between 0 and 365.')
        today = date.today()
        return self.query('SELECT s.id,m.name,m.phone,s.end_date FROM memberships s JOIN members m ON m.id=s.member_id WHERE s.end_date BETWEEN %s AND %s ORDER BY s.end_date', (today.isoformat(),(today+timedelta(days=days)).isoformat()))

    def update_member(self, member_id: int, name: str, phone: str):
        name, phone = name.strip(), phone.strip()
        if not name or not phone or len(name) > 100 or len(phone) > 30:
            raise ValueError('Provide a name and phone within the allowed lengths.')
        if not self.query('SELECT id FROM members WHERE id=%s', (member_id,)):
            raise ValueError('Member does not exist.')
        self.query('UPDATE members SET name=%s,phone=%s WHERE id=%s', (name, phone, member_id), True)
        return {'id': member_id}

    def renew_membership(self, member_id: int, plan_id: int):
        rows = self.query('SELECT MAX(end_date) AS latest FROM memberships WHERE member_id=%s', (member_id,))
        start = date.today()
        if rows[0]['latest']:
            latest = date.fromisoformat(str(rows[0]['latest']))
            start = max(start, latest + timedelta(days=1))
        return self.activate_membership(member_id, plan_id, start.isoformat())

    def membership_report(self):
        rows = self.query('SELECT s.*,m.name,m.phone,p.name AS plan_name,COALESCE((SELECT SUM(amount) FROM payments WHERE membership_id=s.id),0) AS paid FROM memberships s JOIN members m ON m.id=s.member_id JOIN plans p ON p.id=s.plan_id ORDER BY s.end_date DESC')
        today = date.today().isoformat()
        for row in rows:
            row['balance'] = Decimal(str(row['agreed_price'])) - Decimal(str(row['paid']))
            row['status'] = 'Upcoming' if str(row['start_date']) > today else 'Expired' if str(row['end_date']) < today else 'Active'
        return rows

    def dashboard(self):
        rows = self.membership_report()
        return {
            'members': self.query('SELECT COUNT(*) AS n FROM members')[0]['n'],
            'active_members': len({r['member_id'] for r in rows if r['status'] == 'Active'}),
            'total_received': sum((Decimal(str(r['paid'])) for r in rows), Decimal('0')),
            'pending_balance': sum((max(r['balance'], Decimal('0')) for r in rows), Decimal('0')),
            'today_attendance': self.query('SELECT COUNT(*) AS n FROM attendance WHERE attended_on=%s', (date.today().isoformat(),))[0]['n']
        }

    def check_in(self, member_id: int):
        today = date.today().isoformat()
        conn = self.connect()
        try:
            cur = conn.cursor(dictionary=True)
            cur.execute('SELECT id FROM members WHERE id=%s FOR UPDATE', (member_id,))
            if not cur.fetchone():
                raise ValueError('Member does not exist.')
            cur.execute('SELECT id FROM memberships WHERE member_id=%s AND start_date<=%s AND end_date>=%s', (member_id, today, today))
            if not cur.fetchone():
                raise ValueError('An active membership is required for attendance.')
            cur.execute('SELECT id FROM attendance WHERE member_id=%s AND attended_on=%s', (member_id, today))
            existing = cur.fetchone()
            if existing:
                return {'id': existing['id'], 'already_recorded': True}
            cur.execute('INSERT INTO attendance (member_id,attended_on) VALUES (%s,%s)', (member_id, today))
            result = {'id': cur.lastrowid, 'already_recorded': False}
            conn.commit()
            return result
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def attendance_report(self, start_date: str, end_date: str):
        start, end = date.fromisoformat(start_date), date.fromisoformat(end_date)
        if end < start:
            raise ValueError('End date must be on or after start date.')
        return self.query('SELECT a.id,a.member_id,m.name,m.phone,a.attended_on FROM attendance a JOIN members m ON m.id=a.member_id WHERE a.attended_on BETWEEN %s AND %s ORDER BY a.attended_on DESC,a.id DESC', (start.isoformat(), end.isoformat()))

    def payment_history(self, member_id: int):
        return self.query('SELECT p.id,p.membership_id,p.amount,p.reference,p.recorded_at,m.name,m.phone FROM payments p JOIN memberships s ON s.id=p.membership_id JOIN members m ON m.id=s.member_id WHERE s.member_id=%s ORDER BY p.id DESC', (member_id,))
