"""Offline tests for current-weather lookup and input/error handling."""
import unittest
from unittest.mock import Mock
from weather_app import WeatherService, celsius_to_fahrenheit, temperature_text

class TestWeatherHelpers(unittest.TestCase):
    def test_temperature_conversion(self):
        self.assertAlmostEqual(celsius_to_fahrenheit(0), 32)
        self.assertAlmostEqual(celsius_to_fahrenheit(100), 212)
        self.assertEqual(temperature_text(0, "°F"), "32.0 °F")

class TestWeatherService(unittest.TestCase):
    def setUp(self):
        self.session = Mock()
        response = Mock(); response.status_code = 200
        response.json.return_value = {"name":"Delhi", "main":{"temp":30,"feels_like":32,"humidity":40,"pressure":1012}, "wind":{"speed":2}, "weather":[{"description":"clear sky","icon":"01d"}], "sys":{"country":"IN"}, "visibility":10000}
        response.raise_for_status.return_value = None
        self.session.get.return_value = response

    def test_city_search_calls_only_current_weather_api(self):
        result = WeatherService(self.session).get_weather("Delhi", "test-key")
        self.assertEqual(result["current"]["name"], "Delhi")
        self.session.get.assert_called_once()
        self.assertEqual(self.session.get.call_args.kwargs["params"]["q"], "Delhi")
        self.assertEqual(self.session.get.call_args.kwargs["params"]["appid"], "test-key")

    def test_zip_search_uses_zip_parameter(self):
        WeatherService(self.session).get_weather("110001,IN", "test-key")
        self.assertEqual(self.session.get.call_args.kwargs["params"]["zip"], "110001,IN")

    def test_empty_location_and_missing_key_rejected(self):
        with self.assertRaises(ValueError): WeatherService(self.session).get_weather(" ", "test-key")
        with self.assertRaises(ValueError): WeatherService(self.session).get_weather("Delhi", "")
        self.session.get.assert_not_called()

    def test_invalid_zip_format_rejected(self):
        with self.assertRaisesRegex(ValueError, "country code"): WeatherService(self.session).get_weather("110001", "test-key")

    def test_state_abbreviation_rejected_with_example(self):
        with self.assertRaisesRegex(ValueError, "state abbreviation"): WeatherService(self.session).get_weather("UP", "test-key")
        self.session.get.assert_not_called()

    def test_numeric_only_location_rejected(self):
        with self.assertRaisesRegex(ValueError, "number alone"): WeatherService(self.session).get_weather("12345", "test-key")
        self.session.get.assert_not_called()

    def test_mixed_numeric_word_rejected(self):
        with self.assertRaisesRegex(ValueError, "looks invalid"): WeatherService(self.session).get_weather("123abc", "test-key")
        self.session.get.assert_not_called()

    def test_postal_code_country_is_normalized(self):
        WeatherService(self.session).get_weather("110001,in", "test-key")
        self.assertEqual(self.session.get.call_args.kwargs["params"]["zip"], "110001,IN")

    def test_invalid_api_key_message(self):
        response=Mock(); response.status_code=401; self.session.get.return_value=response
        with self.assertRaisesRegex(RuntimeError, "Invalid or inactive"): WeatherService(self.session).get_weather("Delhi", "bad-key")

    def test_city_not_found_message(self):
        response=Mock(); response.status_code=404; self.session.get.return_value=response
        with self.assertRaisesRegex(ValueError, "Location not found"): WeatherService(self.session).get_weather("NoSuchPlace", "test-key")

class TestPayloadAndIcon(unittest.TestCase):
    def test_missing_temperature_is_reported_not_crashed(self):
        session = Mock(); response = Mock(); response.status_code = 200
        response.json.return_value = {"name": "Delhi", "main": {"humidity": 40}, "wind": {"speed": 2}, "weather": [{"description": "clear sky"}]}
        session.get.return_value = response
        with self.assertRaisesRegex(RuntimeError, "incomplete"):
            WeatherService(session).get_weather("Delhi", "test-key")

    def test_icon_download_failure_returns_none(self):
        import requests
        session = Mock(); session.get.side_effect = requests.ConnectionError()
        self.assertIsNone(WeatherService(session).fetch_icon("01d"))

    def test_icon_download_returns_bytes(self):
        session = Mock(); response = Mock(); response.content = b"png-bytes"; session.get.return_value = response
        self.assertEqual(WeatherService(session).fetch_icon("01d"), b"png-bytes")

if __name__ == "__main__": unittest.main()
