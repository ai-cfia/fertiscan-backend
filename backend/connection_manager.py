from flask import Flask
from psycopg_pool import ConnectionPool


class ConnectionManager:
    """
    Manages database connections using a connection pool for a Flask application.

    This class provides methods to get and release connections, manage transactions,
    and handle connection pooling for a PostgreSQL database. It is designed to be
    used as a context manager with the 'with' statement to ensure proper resource management.

    When the app is in testing mode, the manager avoids committing transactions
    and releasing connections back to the pool, allowing for more control over the connection.

    Attributes:
        app (Flask): The Flask application instance.
        pool (ConnectionPool): The connection pool used to manage database connections.
        connection (Connection): The active database connection, if any.
    """

    def __init__(self, app: Flask, pool: ConnectionPool):
        """
        Initializes the ConnectionManager with a Flask app and a connection pool.

        Args:
            app (Flask): The Flask application instance.
            pool (ConnectionPool): The connection pool used to manage database connections.
        """
        self.app = app
        self.pool = pool
        self.connection = None

    def get(self):
        """
        Retrieves a connection from the connection pool.

        If no connection is currently active, a new connection is obtained from the pool.

        Returns:
            Connection: The active database connection.
        """
        if self.connection is None:
            self.pool.check()
            self.connection = self.pool.getconn()
        return self.connection

    def get_cursor(self):
        """
        Retrieves a cursor from the active connection.

        If no connection is currently active, a new connection is obtained from the pool,
        and a cursor is created from it.

        Returns:
            Cursor: A cursor object for executing SQL queries.
        """
        return self.get().cursor()

    def put(self):
        """
        Releases the active connection back to the pool if the Flask application is not
        in testing.
        """
        if not self.app.testing and self.connection is not None:
            self.pool.putconn(self.connection)
            self.connection = None

    def commit(self):
        """
        Commits the current transaction if the Flask application is not in testing mode.
        """
        if not self.app.testing and self.connection is not None:
            self.connection.commit()

    def rollback(self):
        """
        Rolls back the current transaction.
        """
        if self.connection is not None:
            self.connection.rollback()

    def __enter__(self):
        """
        Enters the runtime context related to this object.

        Returns:
            ConnectionManager: The current instance of ConnectionManager.
        """
        return self

    def __exit__(self, exc_type, exc_value, tb):
        """
        Exits the runtime context related to this object.

        Commits the transaction if no exception occurred; otherwise, rolls it back.
        Finally, releases the connection back to the pool.

        Args:
            exc_type (type): The exception type (if any).
            exc_value (Exception): The exception instance (if any).
            tb (traceback): The traceback object (if any).
        """
        if exc_type is None:
            self.commit()
        else:
            self.rollback()
        self.put()
