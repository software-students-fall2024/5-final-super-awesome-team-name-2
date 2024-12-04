from flask import Flask, render_template, request, Response, url_for
import requests
import os

app = Flask(__name__, 
           template_folder='templates',
           static_folder='static')

app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-here')
BACKEND_URL = os.environ.get('BACKEND_URL', 'http://backend:5001')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/<path:path>', methods=['GET', 'POST'])
def proxy_to_backend(path):
    try:
        if request.method == 'GET':
            resp = requests.get(
                f'{BACKEND_URL}/api/{path}',
                cookies=request.cookies
            )
        else:
            resp = requests.post(
                f'{BACKEND_URL}/api/{path}',
                json=request.get_json(),
                cookies=request.cookies
            )
        response = Response(
            resp.content,
            status=resp.status_code,
            content_type=resp.headers['content-type']
        )
        if 'set-cookie' in resp.headers:
            response.headers['set-cookie'] = resp.headers['set-cookie']
        return response
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}, 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)