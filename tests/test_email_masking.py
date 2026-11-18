import unittest

from uri_cardinality_reducer import UriCardinalityReducer


class EmailMaskingTests(unittest.TestCase):
    def test_extract_replaces_email_path_segments(self) -> None:
        reducer = UriCardinalityReducer()

        self.assertEqual(
            "https://example.com/api/users/<EMAIL>/profile",
            reducer.extract("https://example.com/api/users/dave@example.com/profile"),
        )
        self.assertEqual(
            "https://example.com/api/users/<EMAIL>/profile",
            reducer.extract(
                "https://example.com/api/users/john.doe+alerts@example.org/profile"
            ),
        )


class KeyMaskingTests(unittest.TestCase):
    def test_extract_replaces_base64_key_path_segment(self) -> None:
        reducer = UriCardinalityReducer()
        key = (
            "pVqdE79TTLor6ozIEaxRH4fhXDhh7JGS6kGelNF4j9BPN34svXnWlI69EAnpVXWX"
            "qJHjWa9Rp8WROOZeASLeBuwwyLln9TutFvJeBdrmEcBK0KefUPpuWvZMEyIFbjhABEi2VORlavjMOF0kWlczDa=="
        )

        self.assertEqual(
            "https://example.com/api/keys/<KEY>/download",
            reducer.extract(f"https://example.com/api/keys/{key}/download"),
        )


if __name__ == "__main__":
    unittest.main()
