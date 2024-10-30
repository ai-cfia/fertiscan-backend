import unittest

from app.sanitization import custom_secure_filename


class TestCustomSecureFilename(unittest.TestCase):
    def test_spaces_replaced(self):
        self.assertEqual(custom_secure_filename("my file.pdf"), "my_file.pdf")

    def test_path_traversal_removed(self):
        self.assertEqual(custom_secure_filename("../../../etc/passwd"), "passwd")

    def test_special_characters_removed(self):
        self.assertEqual(custom_secure_filename("hello@world!.txt"), "helloworld.txt")

    def test_reserved_keyword_unchanged(self):
        self.assertEqual(custom_secure_filename("CON.txt"), "CON.txt")

    def test_mixed_characters(self):
        self.assertEqual(custom_secure_filename("project#1!.zip"), "project1.zip")

    def test_complex_filename(self):
        self.assertEqual(custom_secure_filename("my<>file|name?.exe"), "myfilename.exe")

    def test_no_changes_needed(self):
        self.assertEqual(
            custom_secure_filename("valid_filename.doc"), "valid_filename.doc"
        )

    def test_sql_injection_semicolon(self):
        self.assertEqual(
            custom_secure_filename("5; DROP TABLE users; --.txt"),
            "5_DROP_TABLE_users_--.txt",
        )

    def test_sql_injection_drop_table(self):
        self.assertEqual(
            custom_secure_filename("DROP Table users;--.csv"), "DROP_Table_users--.csv"
        )


if __name__ == "__main__":
    unittest.main()
