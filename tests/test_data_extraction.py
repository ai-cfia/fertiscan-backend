import unittest
from unittest.mock import MagicMock, patch

from app.controllers.data_extraction import extract_data

class TestExtractData(unittest.TestCase):

    def setUp(self):
        self.settings = MagicMock()

    @patch("app.controllers.data_extraction.analyze")
    def test_extract_data_no_files(self, mock_analyze):
        files = []

        with self.assertRaises(ValueError):
            extract_data(files, self.settings)

        mock_analyze.assert_not_called()

    # @patch("app.controllers.data_extraction.analyze", side_effect=Exception("OCR error"))
    # def test_extract_data_analyze_failure(self, mock_analyze):
    #     files = [b"file1"]

    #     with self.assertRaises(Exception) as ctx:
    #         extract_data(files, self.settings)

    #     self.assertEqual(str(ctx.exception), "OCR error")


if __name__ == "__main__":
    unittest.main()
