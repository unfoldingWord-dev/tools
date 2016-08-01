

import unittest

import gogs.http_utils as http_utils


class HttpUtilsTest(unittest.TestCase):

    def test_append_url1(self):
        base = "https://www.google.com/"
        path = "/images/"
        self.assertEqual(http_utils.append_url(base, path), "https://www.google.com/images/")

    def test_append_url2(self):
        base = "http://hello.world.net"
        path = "great/api/v1"
        self.assertEqual(http_utils.append_url(base, path), "http://hello.world.net/great/api/v1")


if __name__ == "__main__":
    unittest.main()
