from app.database import db

print(db.test_connection())

db.close()
