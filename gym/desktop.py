"""Desktop interface for the existing gym service. Run: python -m gym.desktop."""
import queue
import tkinter as tk
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from decimal import Decimal
from tkinter import ttk, messagebox, filedialog
import csv
from pathlib import Path
from gym.db import gym


class GymApp:
    def __init__(self, root, service=gym):
        self.root, self.service = root, service
        self.pool = ThreadPoolExecutor(max_workers=1)
        self.results = queue.Queue()
        self.busy = False
        self.closing = False
        self.buttons = []
        root.title('Gym Manager')
        root.geometry('1280x780')
        root.minsize(1100, 680)
        root.configure(bg='#eff3f7')
        style = ttk.Style(root)
        style.theme_use('clam')
        style.configure('TFrame', background='#eff3f7')
        style.configure('TLabel', background='#eff3f7', foreground='#183047', font=('Segoe UI', 10))
        style.configure('TButton', font=('Segoe UI', 10), padding=(14, 8))
        style.configure('TNotebook.Tab', font=('Segoe UI', 10), padding=(10, 10))
        style.configure('Treeview', rowheight=30, font=('Segoe UI', 10))
        style.configure('Treeview.Heading', font=('Segoe UI', 10, 'bold'))
        header = tk.Frame(root, bg='#142d44', padx=26, pady=18)
        header.pack(fill='x')
        tk.Label(header, text='GYM MANAGER', font=('Segoe UI', 22, 'bold'), fg='white', bg='#142d44').pack(anchor='w')
        tk.Label(header, text='Members · Membership plans · Payments', font=('Segoe UI', 11), fg='#b8d4e8', bg='#142d44').pack(anchor='w', pady=(4,0))
        self.status = tk.StringVar(value='Ready — choose a tab to get started.')
        notebook = ttk.Notebook(root)
        notebook.pack(fill='both', expand=True, padx=20, pady=18)
        self.dashboard_page(notebook)
        self.members_page(notebook)
        self.plans_page(notebook)
        self.membership_page(notebook)
        self.expiry_page(notebook)
        self.attendance_page(notebook)
        self.reports_page(notebook)
        self.receipts_page(notebook)
        ttk.Label(root, textvariable=self.status, padding=(22, 10)).pack(fill='x')
        root.protocol('WM_DELETE_WINDOW', self.close)
        root.after(100, self.poll)

    def page(self, notebook, name, help_text):
        frame = ttk.Frame(notebook, padding=18)
        notebook.add(frame, text=name)
        ttk.Label(frame, text=help_text, wraplength=950).pack(anchor='w', pady=(0,16))
        return frame

    def fields(self, parent, definitions):
        row=ttk.Frame(parent)
        row.pack(fill='x', pady=(0,12))
        result={}
        for column,(key,label,default) in enumerate(definitions):
            cell=ttk.Frame(row)
            cell.grid(row=0,column=column,sticky='ew',padx=(0,14))
            row.columnconfigure(column,weight=1)
            ttk.Label(cell,text=label).pack(anchor='w',pady=(0,5))
            value=tk.StringVar(value=default)
            ttk.Entry(cell,textvariable=value).pack(fill='x')
            result[key]=value
        return result

    def button(self, parent, label, command):
        button=ttk.Button(parent,text=label,command=command)
        button.pack(side='left',padx=(0,10),pady=(0,12))
        self.buttons.append(button)

    def table(self, parent, columns):
        frame=ttk.Frame(parent)
        frame.pack(fill='both',expand=True,pady=(6,0))
        tree=ttk.Treeview(frame,columns=[key for key,_ in columns],show='headings',selectmode='browse')
        for key,label in columns:
            tree.heading(key,text=label)
            tree.column(key,width=125,anchor='w',stretch=True)
        scroll=ttk.Scrollbar(frame,orient='vertical',command=tree.yview)
        tree.configure(yscrollcommand=scroll.set)
        tree.pack(side='left',fill='both',expand=True)
        scroll.pack(side='right',fill='y')
        return tree

    def fill(self, tree, rows):
        tree.delete(*tree.get_children())
        for row in rows:
            tree.insert('', 'end', values=[str(row.get(key,'')) for key in tree['columns']])
        self.status.set(f'Loaded {len(rows)} record(s).')

    def submit(self, operation, callback=None):
        if self.busy: return
        self.busy=True
        self.status.set('Working…')
        for button in self.buttons: button.state(['disabled'])
        def work():
            try: self.results.put((True,operation(),callback))
            except Exception as exc: self.results.put((False,exc,None))
        self.pool.submit(work)

    def poll(self):
        if self.closing: return
        try:
            ok,value,callback=self.results.get_nowait()
        except queue.Empty: pass
        else:
            self.busy=False
            for button in self.buttons: button.state(['!disabled'])
            if ok:
                self.status.set('Completed successfully.')
                if callback: callback(value)
            else:
                self.status.set('Operation failed. Check the details and try again.')
                # Do not display DB diagnostics which can expose settings or SQL.
                detail=str(value) if isinstance(value,(ValueError,TypeError)) else 'Could not complete the database operation. Check MySQL, your .env settings, and duplicate names, phones or payment references.'
                messagebox.showerror('Gym Manager',detail,parent=self.root)
        self.root.after(100,self.poll)

    def integer(self,value,label):
        try:
            number=int(value)
            if number<=0: raise ValueError()
            return number
        except ValueError: raise ValueError(f'{label} must be a positive whole number.')

    def members_page(self, notebook):
        page=self.page(notebook,'Members','Register a member or search by name / phone. Select a result to copy the member ID to Memberships & Payments.')
        fields=self.fields(page,[('name','Member name',''),('phone','Phone number','')])
        row=ttk.Frame(page);row.pack(fill='x')
        def add():
            name,phone=fields['name'].get(),fields['phone'].get()
            self.submit(lambda:self.service.add_member(name,phone),lambda r:self.created(r,'Member'))
        self.button(row,'Add member',add)
        def edit():
            selected=self.member_tree.selection()
            if not selected:
                messagebox.showinfo('Select member','Select a member in the results first.',parent=self.root)
                return
            member=int(self.member_tree.item(selected[0],'values')[0])
            name,phone=fields['name'].get(),fields['phone'].get()
            self.submit(lambda:self.service.update_member(member,name,phone),lambda r:self.created(r,'Member'))
        self.button(row,'Update selected',edit)
        self.member_edit_fields=fields
        search=self.fields(page,[('query','Search name or phone (empty = latest 100 members)','')])
        row=ttk.Frame(page);row.pack(fill='x')
        def load():
            query=search['query'].get()
            self.submit(lambda:self.service.search_members(query),lambda rows:self.fill(self.member_tree,rows))
        self.button(row,'Search / Refresh',load)
        self.member_tree=self.table(page,[('id','Member ID'),('name','Name'),('phone','Phone')])
        self.member_tree.bind('<<TreeviewSelect>>',self.select_member)

    def plans_page(self, notebook):
        page=self.page(notebook,'Plans','Prices are in INR. Duration is a fixed number of days, rather than a calendar month.')
        fields=self.fields(page,[('name','Plan name',''),('days','Duration (days)','30'),('price','Price (₹)','1000.00')])
        row=ttk.Frame(page);row.pack(fill='x')
        def add():
            name,days,price=(fields[k].get() for k in ('name','days','price'))
            self.submit(lambda:self.service.create_plan(name,self.integer(days,'Duration'),price),lambda r:self.created(r,'Plan'))
        self.button(row,'Create plan',add)
        self.button(row,'Refresh plans',lambda:self.submit(self.service.list_plans,lambda rows:self.fill(self.plan_tree,rows)))
        self.plan_tree=self.table(page,[('id','Plan ID'),('name','Plan name'),('duration_days','Days'),('price','Price (₹)')])
        self.plan_tree.bind('<<TreeviewSelect>>',self.select_plan)

    def membership_page(self, notebook):
        page=self.page(notebook,'Memberships & Payments','Use the IDs from Members and Plans. Select a membership row to record its payment. Payment recording does not charge money.')
        self.membership_fields=self.fields(page,[('member','Member ID',''),('plan','Plan ID',''),('start','Start date (YYYY-MM-DD)',date.today().isoformat())])
        row=ttk.Frame(page);row.pack(fill='x')
        def activate():
            member,plan,start=(self.membership_fields[k].get() for k in ('member','plan','start'))
            if not messagebox.askyesno('Activate membership','Create this membership? Overlapping memberships are allowed.',parent=self.root):return
            self.submit(lambda:self.service.activate_membership(self.integer(member,'Member ID'),self.integer(plan,'Plan ID'),start),lambda r:self.created(r,'Membership'))
        def load():
            member=self.membership_fields['member'].get()
            self.submit(lambda:self.service.memberships(self.integer(member,'Member ID')),lambda rows:self.fill(self.membership_tree,[dict(r,balance=Decimal(str(r['agreed_price']))-Decimal(str(r['paid']))) for r in rows]))
        self.button(row,'Activate membership',activate)
        def renew():
            member,plan=(self.membership_fields[k].get() for k in ('member','plan'))
            if messagebox.askyesno('Renew membership','Renew from the day after the latest membership, or today if expired?',parent=self.root):
                self.submit(lambda:self.service.renew_membership(self.integer(member,'Member ID'),self.integer(plan,'Plan ID')),lambda r:self.created(r,'Membership'))
        self.button(row,'Renew membership',renew)
        self.button(row,'Load member memberships',load)
        self.payment_fields=self.fields(page,[('membership','Membership ID',''),('amount','Payment amount (₹)',''),('reference','Unique receipt reference','')])
        row=ttk.Frame(page);row.pack(fill='x')
        def pay():
            membership,amount,reference=(self.payment_fields[k].get() for k in ('membership','amount','reference'))
            if not messagebox.askyesno('Record payment',f'Record ₹{amount} received, with reference {reference}?',parent=self.root):return
            self.submit(lambda:self.service.record_payment(self.integer(membership,'Membership ID'),amount,reference),lambda r:self.created(r,'Payment'))
        self.button(row,'Record payment',pay)
        self.membership_tree=self.table(page,[('id','Membership ID'),('plan_name','Plan'),('start_date','Start'),('end_date','Expiry'),('agreed_price','Fee (₹)'),('paid','Paid (₹)'),('balance','Balance (₹)')])
        self.membership_tree.bind('<<TreeviewSelect>>',self.select_membership)

    def expiry_page(self, notebook):
        page=self.page(notebook,'Expiry','Show membership records ending today through the next number of days. Expired records are excluded; overlapping memberships appear separately.')
        fields=self.fields(page,[('days','Days ahead (0–365)','7')])
        row=ttk.Frame(page);row.pack(fill='x')
        def load():
            days=fields['days'].get()
            def fetch():
                try: number=int(days)
                except ValueError: raise ValueError('Days must be a whole number from 0 to 365.')
                return self.service.expiring_memberships(number)
            self.submit(fetch,lambda rows:self.fill(self.expiry_tree,rows))
        self.button(row,'Check expiry',load)
        self.expiry_tree=self.table(page,[('id','Membership ID'),('name','Member'),('phone','Phone'),('end_date','Expiry date')])

    def created(self,result,kind):
        extra=' (already recorded)' if result.get('already_recorded') else ''
        self.status.set(f'{kind} ID {result["id"]}{extra}. Refresh the relevant list to see it.')
        if kind=='Member':self.membership_fields['member'].set(str(result['id']))
        elif kind=='Plan':self.membership_fields['plan'].set(str(result['id']))
        elif kind=='Membership':self.payment_fields['membership'].set(str(result['id']))
        messagebox.showinfo('Success',self.status.get(),parent=self.root)

    def select_member(self,event):
        selected=self.member_tree.selection()
        if selected:
            values=self.member_tree.item(selected[0],'values')
            self.membership_fields['member'].set(str(values[0]))
            self.member_edit_fields['name'].set(values[1])
            self.member_edit_fields['phone'].set(values[2])
            self.attendance_fields['member'].set(str(values[0]))
            self.receipt_fields['member'].set(str(values[0]))
    def select_plan(self,event):
        selected=self.plan_tree.selection()
        if selected:self.membership_fields['plan'].set(str(self.plan_tree.item(selected[0],'values')[0]))
    def select_membership(self,event):
        selected=self.membership_tree.selection()
        if selected:self.payment_fields['membership'].set(str(self.membership_tree.item(selected[0],'values')[0]))

    def dashboard_page(self, notebook):
        page=self.page(notebook,'Dashboard','Refresh to see current totals. Active members count unique people; balances are calculated per membership.')
        self.summary=tk.StringVar(value='Click Refresh dashboard to load totals.')
        ttk.Label(page,textvariable=self.summary,font=('Segoe UI',16),justify='left').pack(anchor='w',pady=20)
        row=ttk.Frame(page);row.pack(fill='x')
        def show(data):
            self.summary.set('\n\n'.join(f"{key.replace('_',' ').title()}: {value}" for key,value in data.items()))
        self.button(row,'Refresh dashboard',lambda:self.submit(self.service.dashboard,show))

    def attendance_page(self, notebook):
        page=self.page(notebook,'Attendance','Record one visit per member per day. An active membership is required.')
        self.attendance_fields=self.fields(page,[('member','Member ID',''),('start','From date',date.today().isoformat()),('end','To date',date.today().isoformat())])
        row=ttk.Frame(page);row.pack(fill='x')
        def check():
            member=self.attendance_fields['member'].get()
            self.submit(lambda:self.service.check_in(self.integer(member,'Member ID')),lambda r:self.created(r,'Attendance'))
        def load():
            start,end=(self.attendance_fields[k].get() for k in ('start','end'))
            self.submit(lambda:self.service.attendance_report(start,end),lambda rows:self.fill(self.attendance_tree,rows))
        self.button(row,'Check in today',check)
        self.button(row,'Load attendance',load)
        self.attendance_tree=self.table(page,[('id','Visit ID'),('member_id','Member ID'),('name','Name'),('phone','Phone'),('attended_on','Date')])
        self.button(row,'Export CSV',lambda:self.export_csv(self.attendance_tree))

    def reports_page(self, notebook):
        page=self.page(notebook,'Reports','All memberships, including active, upcoming and expired records. Negative balances represent advance payments.')
        row=ttk.Frame(page);row.pack(fill='x')
        self.button(row,'Refresh report',lambda:self.submit(self.service.membership_report,lambda rows:self.fill(self.report_tree,rows)))
        self.button(row,'Export CSV',lambda:self.export_csv(self.report_tree))
        self.report_tree=self.table(page,[('id','ID'),('name','Member'),('plan_name','Plan'),('end_date','Expiry'),('status','Status'),('agreed_price','Fee'),('paid','Paid'),('balance','Balance')])

    def receipts_page(self, notebook):
        page=self.page(notebook,'Receipts','Load a member’s payment history. Select a payment and save its receipt as a text file.')
        self.receipt_fields=self.fields(page,[('member','Member ID','')])
        row=ttk.Frame(page);row.pack(fill='x')
        def load():
            member=self.receipt_fields['member'].get()
            self.submit(lambda:self.service.payment_history(self.integer(member,'Member ID')),lambda rows:self.fill(self.receipt_tree,rows))
        self.button(row,'Load payments',load)
        self.button(row,'Save selected receipt',self.save_receipt)
        self.button(row,'Export CSV',lambda:self.export_csv(self.receipt_tree))
        self.receipt_tree=self.table(page,[('id','Payment ID'),('membership_id','Membership'),('name','Member'),('phone','Phone'),('amount','Amount INR'),('reference','Reference'),('recorded_at','Recorded at')])

    def export_csv(self, tree):
        if not tree.get_children():
            messagebox.showinfo('Export','Load records before exporting.',parent=self.root)
            return
        path=filedialog.asksaveasfilename(parent=self.root,defaultextension='.csv',filetypes=[('CSV','*.csv')])
        if not path:return
        try:
            with open(path,'w',newline='',encoding='utf-8-sig') as f:
                writer=csv.writer(f)
                writer.writerow(tree['columns'])
                for item in tree.get_children():
                    # Escape spreadsheet formulas in user-entered fields.
                    writer.writerow(["'"+str(v) if str(v).lstrip().startswith(('=','+','-','@')) else v for v in tree.item(item,'values')])
            self.status.set('CSV saved.')
        except OSError:
            messagebox.showerror('Export','Could not save the file. Choose a writable folder.',parent=self.root)

    def save_receipt(self):
        selected=self.receipt_tree.selection()
        if not selected:
            messagebox.showinfo('Receipt','Select a payment first.',parent=self.root)
            return
        values=self.receipt_tree.item(selected[0],'values')
        path=filedialog.asksaveasfilename(parent=self.root,defaultextension='.txt',initialfile=f'receipt-{values[0]}.txt',filetypes=[('Text','*.txt')])
        if not path:return
        text='GYM MANAGER — PAYMENT RECEIPT\n\n'+'\n'.join(f'{key.replace("_"," ").title()}: {value}' for key,value in zip(self.receipt_tree['columns'],values))+'\n\nCurrency: INR\nOffline payment recorded; no online charge was made.\n'
        try:
            Path(path).write_text(text,encoding='utf-8')
            self.status.set('Receipt saved.')
        except OSError:
            messagebox.showerror('Receipt','Could not save the receipt. Choose a writable folder.',parent=self.root)

    def close(self):
        if self.busy:
            messagebox.showinfo('Please wait','Wait for the database operation to finish before closing.',parent=self.root)
            return
        self.closing=True
        self.pool.shutdown(wait=False,cancel_futures=True)
        self.root.destroy()


def main():
    root=tk.Tk()
    GymApp(root)
    root.mainloop()

if __name__=='__main__':main()
