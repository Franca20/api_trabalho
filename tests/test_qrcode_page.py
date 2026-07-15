import unittest

from app import app


class QrCodePageTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_qrcode_page_renders(self):
        response = self.client.get('/qrcode')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Gerar QR Code', response.data)

    def test_qrcode_api_returns_lt_payload(self):
        response = self.client.post(
            '/api/lt/qr',
            json={'lt': 'LT0Q7E02AZ7X1'}
        )
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['lt'], 'LT0Q7E02AZ7X1')
        self.assertEqual(data['qr_text'], 'LT0Q7E02AZ7X1')


if __name__ == '__main__':
    unittest.main()
