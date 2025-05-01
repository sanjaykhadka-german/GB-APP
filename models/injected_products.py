from database import db

class InjectedProducts(db.Model):
    __tablename__ = 'injected_products'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    product_id = db.Column(db.Integer, db.ForeignKey('finished_goods.id'), nullable=False)
    injection_rate = db.Column(db.Float, nullable=False)

    product = db.relationship('FinishedGoods', backref='injected_products')