import unittest

from pydantic import BaseModel, ValidationError

from app.models.bucket_name import MinioBucketName


class MinioBucketTestModel(BaseModel):
    bucket_name: MinioBucketName


class TestMinioBucketNameValidation(unittest.TestCase):
    def test_valid_bucket_names(self):
        valid_names = ["valid-bucket", "my.bucket", "abc-123"]
        for name in valid_names:
            with self.subTest(name=name):
                model = MinioBucketTestModel(bucket_name=name)
                self.assertEqual(model.bucket_name, name)

    def test_invalid_bucket_names(self):
        invalid_names = [
            "InvalidBucket",
            "bad..name",
            "192.168.1.1",
            "xn--reserved",
            "bad-s3alias",
        ]
        for name in invalid_names:
            with self.subTest(name=name):
                with self.assertRaises(ValidationError):
                    MinioBucketTestModel(bucket_name=name)
