import os

from psycopg_pool import ConnectionPool


class ConnectionManager:
    """
    Manages database connections using a connection pool for PostgreSQL.

    This class is used for managing database connections, transactions, and pooling
    efficiently. It can be utilized as a context manager, making sure that resources
    are properly managed (connections are committed, rolled back, and released).

    In testing mode, it avoids committing transactions and releasing connections
    back to the pool, enabling more control over connections.

    Attributes:
        testing (bool): Indicates if the application is in testing mode.
        pool (ConnectionPool): The connection pool for managing database connections.
        connection (Connection): The active database connection, if any.
    """

    def __init__(self, pool: ConnectionPool):
        """
        Initializes the ConnectionManager with a connection pool.

        Args:
            pool (ConnectionPool): The connection pool used to manage database connections.
        """

        if not isinstance(pool, ConnectionPool):
            raise ValueError("A connection pool is required.")

        self.testing = os.getenv("TESTING", "") == "True"
        self.pool = pool
        self.connection = None

    def get(self):
        """
        Retrieves an active connection from the connection pool.

        If no connection is active, it acquires a new one from the pool.

        Returns:
            Connection: An active database connection.
        """
        if self.connection is None:
            self.connection = self.pool.getconn()
        return self.connection

    def get_cursor(self):
        """
        Retrieves a cursor from the active connection.

        If no connection is active, it obtains a new one from the pool
        and creates a cursor from it.

        Returns:
            Cursor: A cursor for executing SQL queries.
        """
        return self.get().cursor()

    def put(self):
        """
        Releases the active connection back to the pool if not in testing mode.

        If in testing mode, the connection is not released to the pool.
        """
        if not self.testing and self.connection is not None:
            self.pool.putconn(self.connection)
            self.connection = None

    def commit(self):
        """
        Commits the current transaction if not in testing mode.
        """
        if not self.testing and self.connection is not None:
            self.connection.commit()

    def rollback(self):
        """
        Rolls back the current transaction, if an active connection exists.
        """
        if self.connection is not None:
            self.connection.rollback()

    def __enter__(self):
        """
        Enters the context and returns the ConnectionManager instance.

        Returns:
            ConnectionManager: The current instance of ConnectionManager.
        """
        return self

    def __exit__(self, exc_type, exc_value, tb):
        """
        Exits the context, managing transactions based on exceptions.

        Commits the transaction if no exception occurred, otherwise rolls it back.
        Finally, releases the connection back to the pool.

        Args:
            exc_type (type): The type of the exception (if any).
            exc_value (Exception): The exception instance (if any).
            tb (traceback): The traceback object (if any).
        """
        if exc_type is None:
            self.commit()
        else:
            self.rollback()
        self.put()
