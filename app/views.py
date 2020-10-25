import datetime
import json

import requests
from flask import render_template, redirect, request

from app import app

PEER_ADDRESS = "http://127.0.0.1:8002"


def fetch_posts():
    """
    Fetch chain from peer and store it locally.
    """
    response = requests.get(f'{PEER_ADDRESS}/chain')
    if response.status_code == 200:
        content = []
        chain = json.loads(response.content)['chain']
        for block in chain:
            for transaction in block['transactions']:
                transaction['index'] = block['index']
                transaction['hash'] = block['pred_hash']
                content.append(transaction)
        return sorted(content, key=lambda x: x['timestamp'], reverse=True)


def string_from_timestamp(timestamp):
    return datetime.datetime.fromtimestamp(timestamp).strftime('%H:%M')


@app.route('/')
def index():
    posts = fetch_posts()
    return render_template('index.html',
                           title='InnoChat',
                           posts=posts,
                           peer_address=PEER_ADDRESS,
                           render_time=string_from_timestamp)


@app.route('/submit', methods=['POST'])
def submit_form():
    """
    Create new transaction.
    """
    data = {
        'author': request.form['author'],
        'content': request.form['content']
    }
    requests.post(
        f'{PEER_ADDRESS}/create-transaction',
        json=data,
        headers={'Content-type': 'application/json'}
    )
    return redirect('/')
