import unittest
from pyring import RingFactory, SimpleFactory


class TestRingFactory(unittest.TestCase):
    def test_cannot_instantiate_without_all_methods(self):
        """Test to check error raised when trying to instantiate RingFactory without get and set methods"""

        class BadFactory(RingFactory):
            pass

        with self.assertRaises(TypeError):
            bad_factory = BadFactory()

        class KindaFactory(RingFactory):
            def get(self):
                ...

        with self.assertRaises(TypeError):
            kinda_factory = KindaFactory()

    def test_works_when_methods_supplied(self):
        """Test to check you can instantiate RingFactory with get and set methods and that they work"""

        class GoodFactory(RingFactory):
            value = None

            def get(self):
                return self.value

            def set(self, value):
                self.value = value

        good_factory = GoodFactory()

        self.assertIsNone(good_factory.get())
        good_factory.set(1)
        self.assertEqual(good_factory.get(), 1)

    def test_simple_factory(self):
        """Test to check you can instantiate SimpleFactory and that get and set methods function as expected"""
        simple_factory = SimpleFactory()

        self.assertIsNone(simple_factory.get())
        simple_factory.set(1)
        self.assertEqual(simple_factory.get(), 1)


if __name__ == "__main__":
    unittest.main()
