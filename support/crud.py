from sqlalchemy.orm import Session
from support import models


def add_event(db: Session, tablename: str, data: object):
    try:
        if tablename == 'plaid':
            event = models.PlaidTable(
                datetime=data['request']['datetime'],
                amount_requested=data['request']['loan_amount'],
                credit_score=data['response']['score'],
                amount_granted=data['response']['loan_amount'],
                loan_risk=data['response']['risk']
            )

        elif tablename == 'coinbase':
            event = models.CoinbaseTable(
                datetime=data['request']['datetime'],
                amount_requested=data['request']['loan_amount'],
                credit_score=data['response']['score'],
                amount_granted=data['response']['loan_amount'],
                loan_risk=data['response']['risk']
            )

        elif tablename == 'covalent':
            event = models.CovalentTable(
                datetime=data['request']['datetime'],
                amount_requested=data['request']['loan_amount'],
                credit_score=data['response']['score'],
                amount_granted=data['response']['loan_amount'],
                loan_risk=data['response']['risk']
            )

        db.add(event)
        db.commit()
        db.refresh(event)

    except Exception as e:
        print(f'\033[31m An error occurred while saving the database: {e}\033[0m')

    finally:
        return
