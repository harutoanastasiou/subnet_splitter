import unittest

from subnet_splitter import split_into, split_for_hosts


class SplitIntoTests(unittest.TestCase):
    def test_split_in_half(self):
        result = split_into("10.0.0.0/24", 2)
        self.assertEqual(result, ["10.0.0.0/25", "10.0.0.128/25"])

    def test_split_into_eighths(self):
        result = split_into("192.168.1.0/24", 8)
        self.assertEqual(
            result,
            [
                "192.168.1.0/27",
                "192.168.1.32/27",
                "192.168.1.64/27",
                "192.168.1.96/27",
                "192.168.1.128/27",
                "192.168.1.160/27",
                "192.168.1.192/27",
                "192.168.1.224/27",
            ],
        )

    def test_split_into_one(self):
        self.assertEqual(split_into("10.1.2.0/24", 1), ["10.1.2.0/24"])

    def test_non_power_of_two_rejected(self):
        with self.assertRaises(ValueError):
            split_into("10.0.0.0/24", 3)

    def test_zero_rejected(self):
        with self.assertRaises(ValueError):
            split_into("10.0.0.0/24", 0)

    def test_negative_rejected(self):
        with self.assertRaises(ValueError):
            split_into("10.0.0.0/24", -2)

    def test_too_many_pieces_rejected(self):
        # /30 has 2 host bits -> at most 4 subnets; requesting 8 forces /33.
        with self.assertRaises(ValueError):
            split_into("10.0.0.0/30", 8)

    def test_non_ipv6_rejected(self):
        with self.assertRaises(ValueError):
            split_into("2001:db8::/32", 2)

    def test_invalid_cidr_rejected(self):
        with self.assertRaises(ValueError):
            split_into("not-a-cidr", 2)

    def test_bool_rejected_as_n(self):
        # bool is a subclass of int; we explicitly reject it.
        with self.assertRaises(ValueError):
            split_into("10.0.0.0/24", True)


class SplitForHostsTests(unittest.TestCase):
    def test_hosts_returns_single_block(self):
        self.assertEqual(split_for_hosts("10.0.0.0/24", 100), ["10.0.0.0/25"])

    def test_hosts_exact_boundary(self):
        # /26 has 62 usable hosts (64 - 2); asking for exactly 62 should
        # pick /26, not the larger /25.
        self.assertEqual(split_for_hosts("10.0.0.0/24", 62), ["10.0.0.0/26"])

    def test_hosts_one_short_of_boundary(self):
        # 61 < 62, so /26 still suffices and is preferred over /25.
        self.assertEqual(split_for_hosts("10.0.0.0/24", 61), ["10.0.0.0/26"])

    def test_hosts_too_many_rejected(self):
        with self.assertRaises(ValueError):
            split_for_hosts("10.0.0.0/30", 5)

    def test_hosts_zero_rejected(self):
        with self.assertRaises(ValueError):
            split_for_hosts("10.0.0.0/24", 0)

    def test_hosts_bool_rejected(self):
        with self.assertRaises(ValueError):
            split_for_hosts("10.0.0.0/24", True)

    def test_hosts_non_ipv6_rejected(self):
        with self.assertRaises(ValueError):
            split_for_hosts("2001:db8::/32", 10)

    def test_hosts_full_parent_used(self):
        # Asking for exactly the parent's capacity returns the parent itself.
        self.assertEqual(split_for_hosts("10.0.0.0/24", 254), ["10.0.0.0/24"])

    def test_hosts_one_more_than_parent_rejected(self):
        with self.assertRaises(ValueError):
            split_for_hosts("10.0.0.0/24", 255)


if __name__ == "__main__":
    unittest.main()
