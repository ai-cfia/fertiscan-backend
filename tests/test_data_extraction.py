import unittest
from typing import BinaryIO
from unittest.mock import MagicMock, mock_open, patch

from app.controllers.data_extraction import extract_data


class TestExtractData(unittest.TestCase):
    def test_no_files_provided_raises_value_error(self):
        # Arrange
        files = {}
        ocr = MagicMock()
        gpt = MagicMock()

        # Act & Assert
        with self.assertRaises(ValueError):
            extract_data(files, ocr, gpt)

    @patch("app.controllers.data_extraction.UPLOAD_FOLDER", new="/mocked/path")
    @patch("os.makedirs")
    @patch("os.path.join")
    @patch("builtins.open", new_callable=mock_open)
    @patch("app.controllers.data_extraction.LabelStorage")
    @patch("app.controllers.data_extraction.analyze")
    def test_multiple_files_handling(
        self,
        mock_analyze,
        mock_label_storage_class,
        mock_open_func,
        mock_path_join,
        mock_makedirs,
    ):
        # Arrange
        mock_storage_instance = mock_label_storage_class.return_value
        files = {
            "file1.jpg": MagicMock(spec=BinaryIO),
            "file2.jpg": MagicMock(spec=BinaryIO),
        }
        ocr = MagicMock()
        gpt = MagicMock()

        # Mock the add_image method
        mock_storage_instance.add_image = MagicMock()

        # Set a return value for analyze
        mock_analyze.return_value = "analyze_result"

        # Set different paths for each file
        mock_path_join.side_effect = [
            "/mocked/path/file1.jpg",
            "/mocked/path/file2.jpg",
        ]

        # Act
        result = extract_data(files, ocr, gpt)

        # Assert
        expected_calls = [
            (("/mocked/path", "file1.jpg"),),
            (("/mocked/path", "file2.jpg"),),
        ]
        mock_path_join.assert_has_calls(expected_calls, any_order=True)

        mock_open_func.assert_any_call("/mocked/path/file1.jpg", "wb")
        mock_open_func.assert_any_call("/mocked/path/file2.jpg", "wb")
        self.assertEqual(mock_open_func().write.call_count, 2)

        mock_storage_instance.add_image.assert_any_call("/mocked/path/file1.jpg")
        mock_storage_instance.add_image.assert_any_call("/mocked/path/file2.jpg")
        self.assertEqual(mock_storage_instance.add_image.call_count, 2)

        mock_analyze.assert_called_once_with(mock_storage_instance, ocr, gpt)
        self.assertEqual(result, "analyze_result")

        # Check that os.makedirs was called
        mock_makedirs.assert_called_once_with("/mocked/path", exist_ok=True)
