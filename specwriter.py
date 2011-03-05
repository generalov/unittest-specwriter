"""
Specwriter twiks output of unittest to be like a specification.
"""
import os
import re
import fnmatch
import unittest
try:
    import colorama
    has_colorama = True
except ImportError:
    has_colorama = False
    class Fore:
        GREEN = ""
        RED = ""
        YELLOW = ""
        RESET = ""


_ORIGINAL_TEXT_TEST_RESULT = unittest._TextTestResult

def patch_unittest():
    """Monkepatch unittest with our TestResult."""
    unittest._TextTestResult = SpecTestResult
    if has_colorama: colorama.init()

def unpatch_unittest():
    """Monkepatch unittest with our TestResult."""
    unittest._TextTestResult = _ORIGINAL_TEXT_TEST_RESULT


class SpecTestResult(unittest.TestResult):
    """A test result class that can print formatted text results to a stream.

    Used by TextTestRunner.
    """
    separator1 = "=" * 70
    separator2 = "-" * 70

    def __init__(self, stream, descriptions, verbosity):
        super(SpecTestResult, self).__init__()
        self.stream = stream
        self.showAll = verbosity > 1
        self.showSpec = verbosity > 2
        self.dots = verbosity == 1
        self.descriptions = descriptions
        self.running = {}
        self.prevTest = None

    def getDescription(self, test):
        if self.descriptions and test.shortDescription():
            return test.shortDescription()
        if self.showSpec:
            meth, cls = str(test).split(" ")
            return self.humanizeTestMethodName(meth) + "."
        return str(test)

    def getCaseDescription(self, test):
        if self.descriptions:
            return self.getTestShortDescription(test) or self.formatCaseDescription(str(test))
        else:
            return self.formatCaseDescription(str(test))

    def startTestCase(self, test):
        if self.showSpec:
            self.stream.writeln("")
            self.stream.writeln("%s:" % self.getCaseDescription(test).rstrip("."))

    def startTest(self, test):
        if not test.__class__ is self.prevTest.__class__:
            self.prevTest = test
            self.startTestCase(test)

        super(SpecTestResult, self).startTest(test)
        if self.showSpec:
            self.stream.write("- ")
        elif self.showAll:
            self.stream.write(self.getDescription(test))
            self.stream.write(" ... ")
            self.stream.flush()

    def addSuccess(self, test):
        super(SpecTestResult, self).addSuccess(test)
        if self.showSpec:
            self.stream.writeln(self.green(self.getDescription(test)))
        elif self.showAll:
            self.stream.writeln("ok")
        elif self.dots:
            self.stream.write(".")
            self.stream.flush()

    def addError(self, test, err):
        type, value, trace = err
        if type is NotImplementedError:
            return self.addSkip(test)

        super(SpecTestResult, self).addError(test, err)
        if self.showSpec:
            self.stream.writeln(self.red(self.getDescription(test)))
        elif self.showAll:
            self.stream.writeln("ERROR")
        elif self.dots:
            self.stream.write("E")
            self.stream.flush()

    def addFailure(self, test, err):
        super(SpecTestResult, self).addFailure(test, err)
        if self.showSpec:
            self.stream.writeln(self.red(self.getDescription(test)))
        elif self.showAll:
            self.stream.writeln("FAIL")
        elif self.dots:
            self.stream.write("F")
            self.stream.flush()

    def addSkip(self, test):
        if self.showSpec:
            self.stream.writeln(self.yellow(self.getDescription(test)))
        elif self.showAll:
            self.stream.writeln("SKIP")
        elif self.dots:
            self.stream.write("S")
            self.stream.flush()

    def printErrors(self):
        if self.dots or self.showAll:
            self.stream.writeln()
        self.printErrorList("ERROR", self.errors)
        self.printErrorList("FAIL", self.failures)

    def printErrorList(self, flavour, errors):
        for test, err in errors:
            self.stream.writeln(self.separator1)
            self.stream.writeln("%s: %s" % (flavour,self.getDescription(test)))
            self.stream.writeln(self.separator2)
            self.stream.writeln("%s" % err)

    # --

    def green(self, text):
        return Fore.GREEN + text + Fore.RESET

    def yellow(self, text):
        return Fore.YELLOW + text + Fore.RESET

    def red(self, text):
        return Fore.RED + text + Fore.RESET

    def formatCaseDescription(self, desc):
        if not self.showSpec:
            return desc
        meth, cls = desc.split(" ")
        return self.humanizeTestClassName(cls[1:-1])

    def getTestShortDescription(self, test):
        doc = test.__class__.__doc__
        return doc and doc.split("\n")[0].strip() or None

    def humanizeTestMethodName(self, name):
        requirement = re.sub("^test?", "", name).replace("_", " ").strip()
        return requirement

    def humanizeTestClassName(self, name):
        path = name.split(".")
        modules, name = map(self.humanizeTestMethodName, path[:-1]), path[-1]
        r = re.compile("Test(Case)?$", re.I)
        subject = ucfirst(unCamel(re.sub(r, "", name)).strip())
        return ". ".join(modules).capitalize() + ". " + subject


def ucfirst(s):
    return s and s[0].capitalize() + s[1:] or s

def unCamel(s):
    words = re.sub("([a-z])(?<![A-Z])([A-Z])","\g<1> \g<2>", s).split(" ")
    return " ".join([
        re.match("[A-Z]{2,}", word) and word or word.lower() for word in words])


def discover(start_dir, pattern="test*.py", top_level_dir=None):
    lsdir = []
    cwd = os.getcwd()
    os.chdir(top_level_dir or start_dir or ".")

    for root, dirs, files in os.walk("."):
        for dname in dirs:
            if os.path.exists(os.path.join(dname, "__init__.py")):
                lsdir.append(os.path.join(root, dname))
        for fname in files:
            if fnmatch.fnmatch(fname, pattern):
                lsdir.append(os.path.join(root, fname))
    modules = [os.path.splitext(path)[0].lstrip(".").lstrip(os.sep).\
                replace(os.path.sep, ".") for path in lsdir]

    testSuite = unittest.TestSuite()
    for name in modules:
        try:
            mod = __import__(name, globals(), locals(), ["suite"])
            suitefn = getattr(mod, "suite")
            testSuite.addTest(suitefn())
        except (ImportError, AttributeError):
            # else, just load all the test cases from the module.
            testSuite.addTest(unittest.defaultTestLoader.loadTestsFromName(name))

    os.chdir(cwd)

    return testSuite


