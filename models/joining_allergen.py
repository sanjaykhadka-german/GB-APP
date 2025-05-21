from database import db

class JoiningAllergen(db.Model):
    __tablename__ = 'joining_allergen'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    fg_code = db.Column(db.String(50), db.ForeignKey('joining.fg_code'), nullable=False)
    allergen_id = db.Column(db.Integer, db.ForeignKey('allergen.allergens_id'), nullable=False)

    __table_args__ = (
        db.UniqueConstraint('fg_code', 'allergen_id', name='uix_joining_allergen'),
        db.Index('idx_joining_allergen_fg_code', 'fg_code'),
        db.Index('idx_joining_allergen_allergen_id', 'allergen_id'),
    )

    def __repr__(self):
        return f"<JoiningAllergen fg_code={self.fg_code}, allergen_id={self.allergen_id}>"