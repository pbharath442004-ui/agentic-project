from app.db import init_db
from app.agent import route

def setup_module():
    init_db()

def test_routes():
    assert route("Create invoice for ABC for 5000")["tool"]=="create_invoice"
    assert route("Show sales report")["tool"]=="sales_report"
    assert route("What is invoice INV-ABC123 status?")["tool"]=="invoice_status"
