from sqlalchemy import Column, Boolean, Integer, Float, String, DateTime, null
from support.database import Base


# database table classes
class PlaidTable(Base):

    __tablename__ = 'plaid'

    event_id = Column(Integer, primary_key=True)
    datetime = Column(DateTime, nullable=False)
    amount_requested = Column(Float, nullable=False)
    credit_score = Column(Float, nullable=False)
    amount_granted = Column(Float, nullable=False)
    loan_risk = Column(String, nullable=False)


class CoinbaseTable(Base):

    __tablename__ = 'coinabse'

    event_id = Column(Integer, primary_key=True)
    datetime = Column(DateTime, nullable=False)
    amount_requested = Column(Float, nullable=False)
    credit_score = Column(Float, nullable=False)
    amount_granted = Column(Float, nullable=False)
    loan_risk = Column(String, nullable=False)


class CovalentTable(Base):

    __tablename__ = 'covalent'

    event_id = Column(Integer, primary_key=True)
    datetime = Column(DateTime, nullable=False)
    amount_requested = Column(Float, nullable=False)
    credit_score = Column(Float, nullable=False)
    amount_granted = Column(Float, nullable=False)
    loan_risk = Column(String, nullable=False)
