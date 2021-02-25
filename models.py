import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, TIME, DATE
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, backref
from sqlalchemy import create_engine
from sqlalchemy.orm import relationship
from app import database_url

engine = create_engine(database_url, echo=False, pool_timeout=20, pool_recycle=299)

Session = sessionmaker(bind=engine)
session = Session()

Base = declarative_base()


class Soldier(Base):
    __tablename__ = "soldier"
    id = Column(Integer, primary_key=True, autoincrement=True)
    class_number = Column(Integer, nullable=False)
    name = Column(String(10), nullable=False)
    soldier_id = Column(String(10), unique=True, nullable=False)
    phone = Column(String(20), unique=True, nullable=False)
    reports_history = relationship('ReportHistory', backref=backref("soldier"), uselist=True)

    def __init__(self, name, soldier_id, phone):
        self.name = name
        self.soldier_id = soldier_id
        self.phone = phone

    def __repr__(self):
        return '<Soldier id %r>' % self.soldier_id


class ReportType(Base):
    __tablename__ = "report_type"
    id = Column(Integer, primary_key=True, autoincrement=True)
    type_name = Column(String(10), unique=True, nullable=False)
    report_time_period = Column(String(10), nullable=False)
    reports_history = relationship('ReportHistory', backref=backref("report_type"), uselist=True)

    def __init__(self, type_name, report_time_period):
        self.type_name = type_name
        self.report_time_period = report_time_period

    def __repr__(self):
        return '<Report type name %r>' % self.type_name


class ReportHistory(Base):
    __tablename__ = "report_history"
    id = Column(Integer, primary_key=True, autoincrement=True)
    report_date = Column(DATE, nullable=False)
    report_time = Column(TIME, nullable=False)
    soldier_id = Column(Integer, ForeignKey('soldier.id'), nullable=False)
    report_type_id = Column(Integer, ForeignKey('report_type.id'), nullable=False)
    location = Column(String(200), nullable=True)
    location_after_ten = Column(String(200), nullable=True)
    body_temperature = Column(String(10), nullable=True)
    symptom = Column(String(50), nullable=True)

    def __init__(self, report_date, report_time, location, location_after_ten, body_temperature, symptom):
        self.report_date = report_date
        self.report_time = report_time
        self.location = location
        self.location_after_ten = location_after_ten
        self.body_temperature = body_temperature
        self.symptom = symptom

    def __repr__(self):
        return '<Report history is %r>' % self.id


def get_report_type_by_id(report_type_id):
    return session.query(ReportType).filter_by(id=report_type_id).first()


def get_soldier(soldier_id):
    return session.query(Soldier).filter_by(soldier_id=soldier_id).first()


def report(report_type_id, soldier_id, location, location_after_ten, body_temperature, symptom):
    report_date = datetime.date.today()
    report_time = datetime.datetime.now()
    standardized_soldier_id = ('12{}'.format(soldier_id))
    try:
        soldier = session.query(Soldier).filter_by(soldier_id=standardized_soldier_id).first()
        report_history = session.query(ReportHistory).filter_by(report_type_id=report_type_id,
                                                                soldier_id=soldier.id).first()
        report_history.report_date = report_date
        report_history.report_time = report_time
        report_history.location = location
        report_history.location_after_ten = location_after_ten
        report_history.body_temperature = body_temperature
        report_history.symptom = symptom
        session.commit()
        session.close()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


