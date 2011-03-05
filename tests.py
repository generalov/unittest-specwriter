import unittest
import textwrap
from StringIO import StringIO


import specwriter


class SpecwriterPatchTest(unittest.TestCase):

    def setUp(self):
        class SelfTest(unittest.TestCase):
            def test_ok(self):
                self.assertTrue(True)

        self.suite = unittest.TestLoader().loadTestsFromTestCase(SelfTest)

    def test_should_patch_and_unpatch_unittest(self):
        params=dict(verbosity=3, descriptions=1)
        output = runTests(self.suite, **params)

        specwriter.patch_unittest()
        spec = runTests(self.suite, **params)
        specwriter.unpatch_unittest()

        restored_output = runTests(self.suite, **params)

        self.assertNotEquals(spec, output)
        self.assertEquals(output, restored_output)


class SpecwriterTest(unittest.TestCase):

    def setUp(self):
        def runSuite(*args):
            suite = unittest.TestSuite()
            loader = unittest.TestLoader()
            suite.addTests([loader.loadTestsFromTestCase(x) for x in args])
            return runTests(suite, verbosity=3, descriptions=1)
            
        self.runSuite = runSuite
        specwriter.patch_unittest()

    def tearDown(self):
        specwriter.unpatch_unittest()

    def test_all(self):
        class AllResultsTest(unittest.TestCase):
            def test_ok(self):
                self.assertTrue(True)

            def test_failed(self):
                self.assertTrue(False)

            def test_skip(self):
                raise NotImplementedError("skipped")

            def test_error(self):
                raise ValueError("error")

        spec = self.runSuite(AllResultsTest)
        self.assertEquals(specBody(spec), textwrap.dedent(
            """
            Main. All results:
            - error.
            - failed.
            - ok.
            - skip.
            """
        )) # methods are seems to be ordered by name.
        self.assertTrue(not 'NotImplementedError' in spec) # skipped
        self.assertTrue('ValueError' in spec)

    def test_should_output_descriptions(self):
        class TestWithDescriptionsTest(unittest.TestCase):
            """Simple description test."""

            def test_method_with_description(self):
                """should be ok."""
                self.assertTrue(True)

        spec = self.runSuite(TestWithDescriptionsTest)
        self.assertEquals(specBody(spec), textwrap.dedent(
            """
            Simple description test:
            - should be ok.
            """
        ))

    def test_should_insert_empty_line_between_specs(self):
        class SomethingTest(unittest.TestCase):
            def test_should_be_ok(self):
                self.assertTrue(True)

        class Something2Test(unittest.TestCase):
            def test_should_be_ok(self):
                self.assertTrue(True)

        spec = self.runSuite(SomethingTest, Something2Test)
        self.assertEquals(specBody(spec), textwrap.dedent(
            """
            Main. Something:
            - should be ok.

            Main. Something2:
            - should be ok.
            """
        ))

    def test_should_to_append_a_dot_after_spec_generated_from_a_method(self):
        class SomethingTest(unittest.TestCase):
            def test_should_be_ok(self):
                self.assertTrue(True)

        spec = self.runSuite(SomethingTest)
        self.assertEquals(specBody(spec), textwrap.dedent(
            """
            Main. Something:
            - should be ok.
            """
        ))

    def test_should_doesnt_append_a_dot_after_spec_generated_from_doc(self):
        class SomethingTest(unittest.TestCase):
            def test_should_be_ok(self):
                """it seems to be good!"""
                self.assertTrue(True)

        spec = self.runSuite(SomethingTest)
        self.assertEquals(specBody(spec), textwrap.dedent(
            """
            Main. Something:
            - it seems to be good!
            """
        ))


def stripStat(spec):
    p = spec.find('\n----')
    return spec[:p] if p >= 0 else spec

def stripExeptions(spec):
    p = spec.find('\n====')
    return spec[:p] if p >= 0 else spec

def specBody(spec):
    return stripStat(stripExeptions(spec))

def runTests(suite, **kwargs):
    stream = StringIO()
    unittest.TextTestRunner(stream, **kwargs).run(suite)
    return stream.getvalue()


if __name__ == '__main__':
    unittest.main()
