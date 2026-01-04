from extensions import db
from datetime import datetime

# ---------------------------------------------------------------------
# Task 2: Create your model here 
# ---------------------------------------------------------------------

class Holding(db.Model):
    __tablename__ = 'holdings'
    
    id = db.Column(db.Integer, primary_key=True)
    ticker = db.Column(db.String(10), unique=True, nullable=False)
    quantity = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f'<Holding {self.ticker}>'

class AnalysisHistory(db.Model):
    __tablename__ = 'analysis_history'
    
    id = db.Column(db.Integer, primary_key=True)
    ticker = db.Column(db.String(10), nullable=False)
    analysis = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<AnalysisHistory {self.ticker}>'
