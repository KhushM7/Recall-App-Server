from flask import Flask, request, jsonify
from email_service import send_email

app = Flask(__name__)

@app.route('/send_email', methods=['POST'])
def send_email_route():
    data = request.json
    to_email = data.get('to_email')
    subject = data.get('subject')
    message = data.get('message')

    if not to_email or not subject or not message:
        return jsonify({'error': 'Missing parameters'}), 400

    if send_email(to_email, subject, message):
        return jsonify({'status': 'Email sent successfully'}), 200
    else:
        return jsonify({'error': 'Failed to send email'}), 500

if __name__ == '__main__':
    app.run(debug=True)
