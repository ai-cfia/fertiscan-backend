import unittest
from unittest.mock import MagicMock, patch

from psycopg import Connection
from psycopg_pool import ConnectionPool

from app.connection_manager import ConnectionManager


class TestConnectionManager(unittest.TestCase):
    def setUp(self):
        self.pool = MagicMock(spec=ConnectionPool)
        self.connection = MagicMock(spec=Connection)
        self.pool.getconn.return_value = self.connection
        self.conn_manager = ConnectionManager(self.pool)

    def tearDown(self):
        self.conn_manager = None

    def test_init_with_none(self):
        """Test that initializing ConnectionManager with None raises ValueError."""
        with self.assertRaises(ValueError) as context:
            ConnectionManager(None)
        self.assertEqual(str(context.exception), "A connection pool is required.")

    def test_init_with_invalid_type(self):
        """Test that initializing ConnectionManager with invalid type raises ValueError."""
        with self.assertRaises(ValueError) as context:
            ConnectionManager("invalid_type")
        self.assertEqual(str(context.exception), "A connection pool is required.")

    def test_get_connection(self):
        """Test that the 'get' method retrieves a connection from the pool."""
        conn = self.conn_manager.get()
        # Assert that the connection returned is the one from the pool
        self.assertEqual(conn, self.connection)
        # Ensure that getconn() was called once to retrieve the connection
        self.pool.getconn.assert_called_once()

        # Call get() again to ensure it does not call getconn() again
        conn_again = self.conn_manager.get()
        # Assert that the same connection is returned
        self.assertEqual(conn_again, self.connection)
        # Ensure getconn() is not called again, confirming reuse of the existing connection
        self.pool.getconn.assert_called_once()

    def test_get_cursor(self):
        """Test that the 'get_cursor' method retrieves a cursor from the active connection."""
        cursor = MagicMock()
        self.connection.cursor.return_value = cursor
        result_cursor = self.conn_manager.get_cursor()
        # Verify that the cursor returned by get_cursor is the same as the mock cursor
        self.assertEqual(result_cursor, cursor)
        # Ensure that the connection's cursor method was called exactly once
        self.connection.cursor.assert_called_once()
        # Verify that the connection was obtained from the pool exactly once
        self.pool.getconn.assert_called_once()

    def test_put_connection_not_testing(self):
        """Test that the 'put' method releases the connection when not in testing mode."""
        self.conn_manager.get()
        self.conn_manager.testing = False
        self.conn_manager.put()
        # Assert that the connection was released back to the pool
        self.pool.putconn.assert_called_once_with(self.connection)
        # Assert that the connection is set to None after releasing
        self.assertIsNone(self.conn_manager.connection)

    def test_put_connection_in_testing(self):
        """Test that the 'put' method does not release the connection when in testing mode."""
        self.conn_manager.get()
        self.conn_manager.testing = True
        self.conn_manager.put()
        # Assert that the connection was not released back to the pool
        self.pool.putconn.assert_not_called()
        # Assert that the connection is still active
        self.assertIsNotNone(self.conn_manager.connection)

    def test_commit_not_testing(self):
        """Test that the 'commit' method commits the transaction when not in testing mode."""
        self.conn_manager.get()
        self.conn_manager.testing = False
        self.conn_manager.commit()
        # Assert that the commit was called on the connection
        self.connection.commit.assert_called_once()

    def test_commit_in_testing(self):
        """Test that the 'commit' method does not commit the transaction when in testing mode."""
        self.conn_manager.get()
        self.conn_manager.testing = True
        self.conn_manager.commit()
        # Assert that the commit was not called on the connection
        self.connection.commit.assert_not_called()

    def test_rollback(self):
        """Test that the 'rollback' method rolls back the current transaction."""
        self.conn_manager.get()  # Activate a connection
        self.conn_manager.rollback()
        self.connection.rollback.assert_called_once()

    @patch.object(ConnectionManager, "commit")
    @patch.object(ConnectionManager, "put")
    def test_context_manager_exit_success(self, mock_put, mock_commit):
        """Test that the context manager commits the transaction and calls put() on successful exit."""
        with self.conn_manager as _:
            pass
        # After exiting, commit() should be called
        mock_commit.assert_called_once()
        # Ensure put() was called
        mock_put.assert_called_once()

    @patch.object(ConnectionManager, "rollback")
    @patch.object(ConnectionManager, "put")
    def test_context_manager_exit_failure(self, mock_put, mock_rollback):
        """Test that the context manager rolls back the transaction and calls put() on exception."""
        with self.assertRaises(Exception):
            with self.conn_manager as _:
                raise Exception("Test Exception")
        # After exiting, rollback() should be called
        mock_rollback.assert_called_once()
        # Ensure put() was called
        mock_put.assert_called_once()
