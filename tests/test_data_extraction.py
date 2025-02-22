import unittest
from unittest.mock import MagicMock, patch
from uuid import uuid4

from psycopg_pool import ConnectionPool

from app.controllers.data_extraction import extract_data
from app.models.label_data import LabelData


class TestExtractData(unittest.IsolatedAsyncioTestCase):
    @patch("app.controllers.data_extraction.LabelStorage")
    @patch("app.controllers.data_extraction.analyze")
    @patch("app.controllers.data_extraction.create_folder")
    @patch("app.controllers.data_extraction.delete_folder")
    async def test_extract_data_success(
        self, mock_delete_folder, mock_create_folder, mock_analyze, mock_label_storage
    ):
        # Setup mocks
        mock_label_storage.return_value.add_image = MagicMock()
        mock_analyze.return_value = MagicMock()
        mock_create_folder.return_value = MagicMock(id=uuid4())

        label_data_mock = MagicMock()
        label_data_mock.model_dump.return_value = {}

        mock_analyze.return_value = label_data_mock

        # Inputs
        cp = MagicMock(spec=ConnectionPool)
        conn_string = "postgres://test_db"
        ocr = MagicMock()
        gpt = MagicMock()
        user_id = uuid4()
        files = [b"file1", b"file2"]

        # Run
        result = await extract_data(cp, conn_string, ocr, gpt, user_id, files)

        # Assertions
        self.assertIsInstance(result, LabelData)
        mock_label_storage.return_value.add_image.assert_called()
        mock_analyze.assert_called_once()
        mock_create_folder.assert_called_once()
        self.assertEqual(result.picture_set_id, mock_create_folder.return_value.id)

    @patch("app.controllers.data_extraction.LabelStorage")
    @patch("app.controllers.data_extraction.analyze")
    @patch("app.controllers.data_extraction.create_folder")
    async def test_extract_data_no_files(
        self, mock_create_folder, mock_analyze, mock_label_storage
    ):
        cp = MagicMock(spec=ConnectionPool)
        conn_string = "postgres://test_db"
        ocr = MagicMock()
        gpt = MagicMock()
        user_id = uuid4()
        files = []

        with self.assertRaises(ValueError):
            await extract_data(cp, conn_string, ocr, gpt, user_id, files)

        mock_label_storage.assert_not_called()
        mock_analyze.assert_not_called()
        mock_create_folder.assert_not_called()

    @patch("app.controllers.data_extraction.LabelStorage")
    @patch(
        "app.controllers.data_extraction.analyze", side_effect=Exception("OCR error")
    )
    @patch("app.controllers.data_extraction.create_folder")
    @patch("app.controllers.data_extraction.delete_folder")
    async def test_extract_data_analyze_failure(
        self, mock_delete_folder, mock_create_folder, mock_analyze, mock_label_storage
    ):
        mock_create_folder.return_value = MagicMock(id=uuid4())

        cp = MagicMock(spec=ConnectionPool)
        conn_string = "postgres://test_db"
        ocr = MagicMock()
        gpt = MagicMock()
        user_id = uuid4()
        files = [b"file1"]

        with self.assertRaises(Exception) as ctx:
            await extract_data(cp, conn_string, ocr, gpt, user_id, files)

        self.assertEqual(str(ctx.exception), "OCR error")
        mock_delete_folder.assert_called_once_with(
            cp, conn_string, user_id, mock_create_folder.return_value.id
        )

    @patch("app.controllers.data_extraction.LabelStorage")
    @patch("app.controllers.data_extraction.analyze")
    @patch(
        "app.controllers.data_extraction.create_folder",
        side_effect=Exception("DB error"),
    )
    @patch("app.controllers.data_extraction.log_error")
    async def test_extract_data_create_folder_failure(
        self, mock_log_error, mock_create_folder, mock_analyze, mock_label_storage
    ):
        label_data_mock = MagicMock()
        label_data_mock.model_dump.return_value = {}
        mock_analyze.return_value = label_data_mock

        cp = MagicMock(spec=ConnectionPool)
        conn_string = "postgres://test_db"
        ocr = MagicMock()
        gpt = MagicMock()
        user_id = uuid4()
        files = [b"file1"]

        result = await extract_data(cp, conn_string, ocr, gpt, user_id, files)

        self.assertIsInstance(result, LabelData)
        self.assertIsNone(result.picture_set_id)
        mock_log_error.assert_called_once_with(mock_create_folder.side_effect)


if __name__ == "__main__":
    unittest.main()
