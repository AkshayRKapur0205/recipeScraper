from flask import Flask, request, jsonify
from recipe_scrapers import scrape_me
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return 'Recipe Scraper API is running. Use /scrape?url=...'


@app.route('/scrape', methods=['GET'])
def scrape():
    url = request.args.get('url')
    if not url:
        return jsonify({'error': 'URL parameter is required'}), 400

    try:
        scraper = scrape_me(url)
        return jsonify({
            'title': scraper.title(),
            'total_time': scraper.total_time(),
            'yields': scraper.yields(),
            'ingredients': scraper.ingredients(),
            'instructions': scraper.instructions(),
            'image': scraper.image(),
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
