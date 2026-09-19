from app.db import init_db
from app.tools import create_invoice, invoice_status, cancel_invoice, send_payment, sales_report

def setup_module():
    init_db()

def test_invoice_flow():
    x=create_invoice("Test Customer",100)
    iid=x["invoice_id"]
    assert invoice_status(iid)["invoice"]["status"]=="OPEN"
    assert send_payment(iid)["success"]
    assert invoice_status(iid)["invoice"]["status"]=="PAID"

def test_cancel():
    x=create_invoice("Cancel Customer",50)
    assert cancel_invoice(x["invoice_id"])["status"]=="CANCELLED"

def test_report():
    assert sales_report()["success"]
