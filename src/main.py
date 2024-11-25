from flask import Flask, request, jsonify
import requests
import redis
import os
import json
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

r = redis.Redis(host='redis', port=6379)

API_KEY = os.getenv('API_KEY', 'your-default-api-key')
CACHE_DURATION = int(os.getenv('CACHE_DURATION', 300))

print(f'API_KEY: {API_KEY}')
print(f'CACHE_DURATION: {CACHE_DURATION}')

@app.route('/define', methods=['GET'])
def get_definition():
    word = request.args.get('word')
    if not word:
        print("No word provided")
        return jsonify({"error": "Word parameter is missing"}), 400

    cached_definition = r.get(word)
    if cached_definition:
        print(f"Found cached definition for {word}")
        return jsonify({"source": "redis", "definition": json.loads(cached_definition)})

    headers = {'X-Api-Key': API_KEY}
    api_url = 'https://api.api-ninjas.com/v1/dictionary?word={}'.format(word)
    response = requests.get(api_url, headers=headers)
    
    print(f'Dictionary API response status code: {response.status_code}')
    print(f'Dictionary API response text: {response.text}')
    
    if response.status_code == requests.codes.ok:
        definition = response.json()
        r.setex(word, CACHE_DURATION, json.dumps(definition))
        return jsonify({"source": "ninjas-api", "definition": definition})
    else:
        print(f'Failed to fetch definition: {response.status_code}')
        return jsonify({"error": f"Failed to fetch definition: {response.status_code}"}), response.status_code

@app.route('/random', methods=['GET'])
def get_random_word_and_definition():
    headers = {'X-Api-Key': API_KEY}
    api_url = 'https://api.api-ninjas.com/v1/randomword'
    response = requests.get(api_url, headers=headers)

    # Log status code and response content
    print(f'Status Code (Random Word): {response.status_code}')
    print(f'Response Text (Random Word): {response.text}')

    if response.status_code == requests.codes.ok:
        try:
            random_word = response.json().get('word')
            print(f'Random word: {random_word}')
            if isinstance(random_word, list):
                random_word = random_word[0]  # Extract the word if it's a list
            random_word = str(random_word)  # Ensure the word is a string
        except ValueError as e:
            print(f'Error decoding JSON: {e}')
            return jsonify({"error": "Error decoding JSON response from random word API"}), 500

        if not random_word:
            print("Random word API returned empty response")
            return jsonify({"error": "Random word API returned empty response"}), 500

        # Now fetch the definition for the random word using the get_definition logic
        cached_definition = r.get(random_word)
        if cached_definition:
            print(f"Found cached definition for {random_word}")
            return jsonify({"source": "redis", "word": random_word, "definition": json.loads(cached_definition)})

        api_url = 'https://api.api-ninjas.com/v1/dictionary?word={}'.format(random_word)
        response = requests.get(api_url, headers=headers)

        # Log status code and response content for dictionary API call
        print(f'Status Code (Definition): {response.status_code}')
        print(f'Response Text (Definition): {response.text}')
        
        if response.status_code == requests.codes.ok:
            definition = response.json()
            r.setex(random_word, CACHE_DURATION, json.dumps(definition))
            return jsonify({"source": "ninjas-api", "word": random_word, "definition": definition})
        else:
            print(f'Failed to fetch definition for {random_word}: {response.status_code}')
            return jsonify({"error": f"Failed to fetch definition: {response.status_code}"}), response.status_code
    else:
        print(f'Failed to fetch random word: {response.status_code}')
        return jsonify({"error": f"Failed to fetch random word: {response.status_code}"}), response.status_code

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)))
