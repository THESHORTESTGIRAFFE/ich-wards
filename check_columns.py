from app import create_app, db
from app.models.models import Patient

app = create_app()
with app.app_context():
    # Get the columns from the Patient model
    print("Patient table columns:")
    for column in Patient.__table__.columns:
        print(f"  - {column.name}: {column.type}")
