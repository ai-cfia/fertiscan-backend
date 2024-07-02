import unittest
from backend import Token, create_label_id, check_user

class TestToken(unittest.TestCase):
    
    def test_default_header(self):
        token = Token()
        self.assertEqual(token.user_id, "default_user")
        self.assertEqual(token.label_id, "0")
    
    def test_custom_header(self):
        token = Token(header="Basic custom_user:1234")
        self.assertEqual(token.user_id, "custom_user")
        self.assertEqual(token.label_id, "1234")
    
    def test_invalid_authentication_scheme(self):
        with self.assertRaises(NotImplementedError) as context:
            Token(header="Bearer token")
        self.assertTrue("Unsupported authentitcation scheme: Bearer" in str(context.exception))
    
    def test_missing_label_id(self):
        with self.assertRaises(KeyError) as context:
            Token(header="Basic user:")
        self.assertTrue("The label_id is missing" in str(context.exception))
    
    def test_str_method(self):
        token = Token(header="Basic user:1234")
        self.assertEqual(str(token), "user:1234")
    
    def test_eq_method(self):
        token1 = Token(header="Basic user:1234")
        token2 = Token(header="Basic user:1234")
        self.assertEqual(token1, token2)
    
    def test_not_eq_method(self):
        token1 = Token(header="Basic user:1234")
        token2 = Token(header="Basic user:5678")
        self.assertNotEqual(token1, token2)
    
    def test_hash_method(self):
        token = Token(header="Basic user:1234")
        self.assertEqual(hash(token), hash("user:1234"))

    def test_create_label_id(self):
        label_id = create_label_id()
        self.assertIsInstance(label_id, str)
        self.assertTrue(label_id.startswith('0x'))
    
    def test_check_user_not_implemented(self):
        with self.assertRaises(NotImplementedError):
            check_user("some_user")

if __name__ == "__main__":
    unittest.main()
