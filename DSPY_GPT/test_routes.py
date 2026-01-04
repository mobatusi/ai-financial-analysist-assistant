import unittest
import json
from app import app, db

class TestRoutes(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['DEBUG'] = False
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()
        with app.app_context():
            db.create_all()

    def test_analyze_valid_ticker(self):
        """Test /api/analyze with a valid ticker."""
        response = self.client.post('/api/analyze', 
                                   data=json.dumps({'ticker': 'AAPL'}),
                                   content_type='application/json')
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['status'], 'ok')
        self.assertIn('stock', data)
        self.assertIn('insight', data)
        self.assertEqual(data['stock']['name'], 'Apple Inc.')

    def test_analyze_empty_ticker(self):
        """Test /api/analyze with an empty ticker."""
        response = self.client.post('/api/analyze', 
                                   data=json.dumps({'ticker': ''}),
                                   content_type='application/json')
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'error')

    def test_analyze_invalid_ticker(self):
        """Test /api/analyze with an invalid ticker (404)."""
        response = self.client.post('/api/analyze', 
                                   data=json.dumps({'ticker': 'INVALID_TICKER_123'}),
                                   content_type='application/json')
        self.assertEqual(response.status_code, 404)

    def test_insight_summary_no_session(self):
        """Test /insight_summary without a session (should show error page)."""
        response = self.client.get('/insight_summary')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Insight Not Available', response.data)

    def test_insight_summary_with_session(self):
        """Test /insight_summary with a session."""
        with self.client.session_transaction() as sess:
            sess['latest_analysis'] = {
                'ticker': 'TSLA',
                'company': 'Tesla, Inc.',
                'price': 250.0,
                'change_pct': 2.5,
                'pe_ratio': 70.0,
                'beta': 2.0,
                'insight': '### Analysis\nTesla is leading the EV market.'
            }
        response = self.client.get('/insight_summary')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Tesla, Inc.', response.data)
        self.assertIn(b'TSLA', response.data)
        # Check if markdown was converted (### Analysis -> <h3>Analysis</h3> or similar)
        self.assertIn(b'Analysis', response.data)

    def test_portfolio_add_new(self):
        """Test adding a new holding."""
        response = self.client.post('/api/portfolio',
                                   data=json.dumps({'ticker': 'MSFT', 'quantity': 10.5}),
                                   content_type='application/json')
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['ok'])
        self.assertEqual(data['ticker'], 'MSFT')
        self.assertEqual(data['quantity'], 10.5)

    def test_portfolio_update_existing(self):
        """Test updating an existing holding (increment quantity)."""
        # Initial add
        self.client.post('/api/portfolio',
                         data=json.dumps({'ticker': 'AAPL', 'quantity': 50.0}),
                         content_type='application/json')
        # Update
        response = self.client.post('/api/portfolio',
                                   data=json.dumps({'ticker': 'AAPL', 'quantity': 25.0}),
                                   content_type='application/json')
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['quantity'], 75.0)

    def test_portfolio_add_invalid_data(self):
        """Test validation errors for /api/portfolio."""
        # Missing ticker
        response = self.client.post('/api/portfolio',
                                   data=json.dumps({'ticker': '', 'quantity': 10}),
                                   content_type='application/json')
        self.assertEqual(response.status_code, 400)

        # Invalid quantity
        response = self.client.post('/api/portfolio',
                                   data=json.dumps({'ticker': 'TSLA', 'quantity': -5}),
                                   content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_portfolio_delete_success(self):
        """Test deleting a holding."""
        # Add first
        self.client.post('/api/portfolio',
                         data=json.dumps({'ticker': 'GOOGL', 'quantity': 5}),
                         content_type='application/json')
        # Delete
        response = self.client.post('/api/portfolio/delete',
                                   data=json.dumps({'ticker': 'GOOGL'}),
                                   content_type='application/json')
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['ok'])

    def test_portfolio_delete_not_found(self):
        """Test deleting a non-existent holding."""
        response = self.client.post('/api/portfolio/delete',
                                   data=json.dumps({'ticker': 'NON_EXISTENT'}),
                                   content_type='application/json')
        self.assertEqual(response.status_code, 404)

    def test_portfolio_report_pdf(self):
        """Test the /report/portfolio.pdf route."""
        # Add a holding first
        self.client.post('/api/portfolio',
                         data=json.dumps({'ticker': 'AAPL', 'quantity': 10}),
                         content_type='application/json')
        
        response = self.client.get('/report/portfolio.pdf')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, 'application/pdf')
        self.assertIn('attachment', response.headers.get('Content-Disposition', ''))
        self.assertIn('portfolio_report.pdf', response.headers.get('Content-Disposition', ''))
        # PDF headers usually start with %PDF
        self.assertTrue(response.data.startswith(b'%PDF'))

if __name__ == '__main__':
    unittest.main()
