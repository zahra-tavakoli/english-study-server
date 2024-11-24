from flask import Flask, request, jsonify
import requests
import redis
import os
import json

app = Flask(__name__)

r = redis.Redis(host='redis', port=6379)

API_KEY = os.getenv('API_KEY', 'UWXfvcz4BGAeql97w3pccg==IUWZ1sTD3P0NFHcN')
CACHE_DURATION = int(os.getenv('CACHE_DURATION', 300))

@app.route('/define', methods=['GET'])
def get_definition():
    word = request.args.get('word')
    if not word:
        return jsonify({"error": "Word parameter is missing"}), 400

    cached_definition = r.get(word)
    if cached_definition:
        return jsonify({"source": "redis", "definition": json.loads(cached_definition)})

    headers = {'X-Api-Key': API_KEY}
    response = requests.get(f'https://api-ninjas.com/api/dictionary?word={word}', headers=headers)

    if response.status_code != 200:
        return jsonify({"error": "Failed to fetch definition"}), response.status_code

    definition = response.json()
    r.setex(word, CACHE_DURATION, json.dumps(definition))
    return jsonify({"source": "ninjas-api", "definition": definition})

@app.route('/random', methods=['GET'])
def get_random_word():
    headers = {'X-Api-Key': API_KEY}
    response = requests.get('https://api-ninjas.com/api/randomword', headers=headers)

    if response.status_code != 200:
        return jsonify({"error": "Failed to fetch random word"}), response.status_code

    random_word = response.json()['word']
    cached_definition = r.get(random_word)
    if cached_definition:
        return jsonify({"source": "redis", "word": random_word, "definition": json.loads(cached_definition)})

    response = requests.get(f'https://api-ninjas.com/api/dictionary?word={random_word}', headers=headers)

    if response.status_code != 200:
        return jsonify({"error": "Failed to fetch definition"}), response.status_code

    definition = response.json()
    r.setex(random_word, CACHE_DURATION, json.dumps(definition))
    return jsonify({"source": "ninjas-api", "word": random_word, "definition": definition})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)))
