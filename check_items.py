from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:german@localhost/gbdb'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class ItemMaster(db.Model):
    __tablename__ = 'item_master'
    id = db.Column(db.Integer, primary_key=True)
    item_code = db.Column(db.String(20))
    description = db.Column(db.String(255))
    item_type = db.Column(db.String(20))

with app.app_context():
    print("\nFinished Goods:")
    finished_goods = ItemMaster.query.filter_by(item_type='finished_good').all()
    for item in finished_goods:
        print(f"{item.item_code}: {item.description}")

    print("\nRaw Materials:")
    raw_materials = ItemMaster.query.filter_by(item_type='raw_material').all()
    for item in raw_materials:
        print(f"{item.item_code}: {item.description}") 