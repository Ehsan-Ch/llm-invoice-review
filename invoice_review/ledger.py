"""Local review state. This records decisions; it never initiates a payment."""
import hashlib
import json
from pathlib import Path
import sqlite3
from datetime import datetime,timezone
from .core import validate

class Ledger:
    def __init__(self,path):
        Path(path).parent.mkdir(parents=True,exist_ok=True)
        self.db=sqlite3.connect(path);self.db.row_factory=sqlite3.Row
        self.db.executescript('''CREATE TABLE IF NOT EXISTS invoices(
          id TEXT PRIMARY KEY, text TEXT NOT NULL, result TEXT NOT NULL,
          status TEXT NOT NULL DEFAULT 'PENDING',version INTEGER NOT NULL DEFAULT 0);
          CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY AUTOINCREMENT,
          invoice_id TEXT NOT NULL,action TEXT NOT NULL,actor TEXT NOT NULL,reason TEXT NOT NULL,at TEXT NOT NULL);''')
    def close(self):self.db.close()
    def add(self,text,result):
        fingerprint=hashlib.sha256(text.replace('\r\n','\n').strip().encode()).hexdigest()
        with self.db:
            cur=self.db.execute('INSERT OR IGNORE INTO invoices(id,text,result) VALUES(?,?,?)',(fingerprint,text,json.dumps(result)))
            if cur.rowcount:self._event(fingerprint,'IMPORT','system','Imported for human review.')
        return {'id':fingerprint,'created':bool(cur.rowcount)}
    def _event(self,id,action,actor,reason):
        self.db.execute('INSERT INTO events(invoice_id,action,actor,reason,at) VALUES(?,?,?,?,?)',
                        (id,action,actor,reason,datetime.now(timezone.utc).isoformat()))
    def list(self):
        return [dict(row) for row in self.db.execute('SELECT id,status,version,result FROM invoices ORDER BY rowid')]
    def audit(self,id):
        return [dict(row) for row in self.db.execute('SELECT * FROM events WHERE invoice_id=? ORDER BY id',(id,))]
    def review(self,id,action,version,actor,reason):
        if action not in ('approve','reject','reopen'):raise ValueError('Unknown review action.')
        if not isinstance(actor,str) or not 1<=len(actor.strip())<=80:raise ValueError('Supply an actor label.')
        if not isinstance(reason,str) or not 1<=len(reason.strip())<=500:raise ValueError('Supply a review reason.')
        if type(version) is not int or version<0:raise ValueError('Supply the current integer record version.')
        with self.db:
            self.db.execute('BEGIN IMMEDIATE')
            row=self.db.execute('SELECT * FROM invoices WHERE id=?',(id,)).fetchone()
            if not row:raise ValueError('Unknown invoice.')
            if row['version']!=version:raise ValueError('Stale version. Reload the record before reviewing.')
            if action=='reopen':
                if row['status']=='PENDING':raise ValueError('Invoice is already pending.')
                target='PENDING'
            else:
                if row['status']!='PENDING':raise ValueError('Reopen the invoice before another decision.')
                if action=='approve':
                    result=json.loads(row['result'])
                    checked=validate(row['text'],result.get('extracted',{}))
                    if result.get('status')!='CHECKS_PASSED' or checked['status']!='CHECKS_PASSED':
                        raise ValueError('Approval blocked: resolve extraction or source issues outside this queue, then import corrected text.')
                target=action.upper()+'D' if action=='approve' else 'REJECTED'
            self.db.execute('UPDATE invoices SET status=?,version=version+1 WHERE id=?',(target,id))
            self._event(id,action.upper(),actor.strip(),reason.strip())
        return {'id':id,'status':target,'version':version+1}
