from .database import SessionLocal, Base, engine
from .models import DiagnosticCentre, DiagnosticTest
Base.metadata.create_all(engine)
db=SessionLocal()
if not db.query(DiagnosticCentre).first():
    c=DiagnosticCentre(name='EVE Diagnostics',location='Greater Noida'); db.add(c); db.flush(); db.add_all([DiagnosticTest(name='CBC',price=500,centre_id=c.id),DiagnosticTest(name='Thyroid Profile',price=800,centre_id=c.id)]); db.commit()
print('Seed complete')
