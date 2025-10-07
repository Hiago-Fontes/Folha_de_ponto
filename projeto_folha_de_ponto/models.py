from datetime import datetime
from extensions import db


class Employee(db.Model):
    __tablename__ = 'employee'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False, unique=True)
    setor = db.Column(db.String(100), nullable=True)
    time_entries = db.relationship('TimeEntry', backref='employee', cascade='all, delete-orphan', lazy='dynamic')

    def __repr__(self):
        return f'<Employee {self.name}>'

    def entries_between(self, start, end):
        # retorna Query/List de TimeEntry entre start e end (inclusive)
        return self.time_entries.filter(TimeEntry.timestamp >= start, TimeEntry.timestamp <= end).order_by(TimeEntry.timestamp)


class TimeEntry(db.Model):
    __tablename__ = 'time_entry'
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    entry_type = db.Column(db.String(10), nullable=False)  # 'entrada' ou 'saida'
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f'<TimeEntry {self.employee.name} {self.entry_type} {self.timestamp}>'