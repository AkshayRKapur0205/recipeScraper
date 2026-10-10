import unittest
from unittest.mock import patch

import app as recipe_api


class RecipeApiTests(unittest.TestCase):
    def setUp(self):
        scrape_me_patch = patch("app.scrape_me")
        self.mock_scrape_me = scrape_me_patch.start()
        self.addCleanup(scrape_me_patch.stop)
        self.client = recipe_api.app.test_client()
        self.url = "https://recipes.example/lemon-pasta?source=test&servings=2"
        self.recipe = {
            "title": "Lemon pasta",
            "total_time": 35,
            "yields": "2 servings",
            "ingredients": [
                "200 g spaghetti",
                "1 lemon",
                "2 tbsp olive oil",
            ],
            "instructions": (
                "1. Cook the pasta.\n2. Toss with lemon and olive oil."
            ),
            "image": "https://recipes.example/lemon-pasta.jpg",
        }
        self.scraper = self.mock_scrape_me.return_value
        for field, value in self.recipe.items():
            getattr(self.scraper, field).return_value = value

    def test_home_returns_running_message(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "text/html")
        self.assertEqual(
            response.get_data(as_text=True),
            "Recipe Scraper API is running. Use /scrape?url=...",
        )
        self.mock_scrape_me.assert_not_called()

    def test_scrape_preserves_fields_and_forwards_decoded_url(self):
        response = self.client.get("/scrape", query_string={"url": self.url})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/json")
        self.assertEqual(response.get_json(), self.recipe)
        self.mock_scrape_me.assert_called_once_with(self.url)
        for field in self.recipe:
            getattr(self.scraper, field).assert_called_once_with()

    def test_missing_or_empty_url_returns_json_400_without_scraping(self):
        for query in ({}, {"url": ""}):
            with self.subTest(query=query):
                response = self.client.get("/scrape", query_string=query)

                self.assertEqual(response.status_code, 400)
                self.assertEqual(response.mimetype, "application/json")
                self.assertEqual(
                    response.get_json(), {"error": "URL parameter is required"}
                )
                self.mock_scrape_me.assert_not_called()

    def test_parser_exception_returns_existing_json_500(self):
        self.mock_scrape_me.side_effect = RuntimeError("Unable to parse recipe")

        response = self.client.get("/scrape", query_string={"url": self.url})

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.mimetype, "application/json")
        self.assertEqual(response.get_json(), {"error": "Unable to parse recipe"})
        self.mock_scrape_me.assert_called_once_with(self.url)

    def test_metadata_exception_returns_existing_json_500(self):
        self.scraper.ingredients.side_effect = ValueError(
            "Ingredient data is unavailable"
        )

        response = self.client.get("/scrape", query_string={"url": self.url})

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.mimetype, "application/json")
        self.assertEqual(
            response.get_json(), {"error": "Ingredient data is unavailable"}
        )
        self.mock_scrape_me.assert_called_once_with(self.url)
        self.scraper.ingredients.assert_called_once_with()

    def test_post_is_rejected_without_scraping(self):
        for path in ("/", "/scrape"):
            with self.subTest(path=path):
                response = self.client.post(path, query_string={"url": self.url})

                self.assertEqual(response.status_code, 405)
                self.assertEqual(response.mimetype, "text/html")
                self.mock_scrape_me.assert_not_called()

    def test_head_scrapes_without_returning_a_body(self):
        response = self.client.head("/scrape", query_string={"url": self.url})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/json")
        self.assertEqual(response.data, b"")
        self.mock_scrape_me.assert_called_once_with(self.url)

    def test_options_reports_allowed_methods_without_scraping(self):
        for path in ("/", "/scrape"):
            with self.subTest(path=path):
                response = self.client.options(path)

                self.assertEqual(response.status_code, 200)
                allowed_methods = {
                    method.strip() for method in response.headers["Allow"].split(",")
                }
                self.assertEqual(allowed_methods, {"GET", "HEAD", "OPTIONS"})
                self.mock_scrape_me.assert_not_called()
