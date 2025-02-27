import unittest
from unittest.mock import MagicMock, patch

from app.controllers.data_extraction import extract_data
from app.models.label_data import LabelData


class TestExtractData(unittest.TestCase):
    @patch("app.controllers.data_extraction.LabelStorage")
    @patch("app.controllers.data_extraction.analyze")
    def test_extract_data_success(self, mock_analyze, mock_label_storage):
        # Setup mocks
        mock_label_storage.return_value.add_image = MagicMock()
        label_data_mock = MagicMock()
        label_data_mock.model_dump.return_value = {}

        mock_analyze.return_value = label_data_mock

        # Inputs
        ocr = MagicMock()
        gpt = MagicMock()
        files = [b"file1", b"file2"]

        # Run
        result = extract_data(ocr, gpt, files)

        # Assertions
        self.assertIsInstance(result, LabelData)
        mock_label_storage.return_value.add_image.assert_called()
        mock_analyze.assert_called_once()

    @patch("app.controllers.data_extraction.LabelStorage")
    @patch("app.controllers.data_extraction.analyze")
    def test_extract_data_no_files(self, mock_analyze, mock_label_storage):
        ocr = MagicMock()
        gpt = MagicMock()
        files = []

        with self.assertRaises(ValueError):
            extract_data(ocr, gpt, files)

        mock_label_storage.assert_not_called()
        mock_analyze.assert_not_called()

    @patch("app.controllers.data_extraction.LabelStorage")
    @patch("app.controllers.data_extraction.analyze", side_effect=Exception("OCR error"))
    def test_extract_data_analyze_failure(self, mock_analyze, mock_label_storage):
        ocr = MagicMock()
        gpt = MagicMock()
        files = [b"file1"]

        with self.assertRaises(Exception) as ctx:
            extract_data(ocr, gpt, files)

        self.assertEqual(str(ctx.exception), "OCR error")


if __name__ == "__main__":
    unittest.main()
