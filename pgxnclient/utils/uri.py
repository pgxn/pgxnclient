"""
Simple implementation of URI-Templates
(http://bitworking.org/projects/URI-Templates/).

Some bits are inspired by or based on:

    * Joe Gregorio's example implementation
      (http://code.google.com/p/uri-templates/)

    * Addressable (http://addressable.rubyforge.org/)
    
Simple usage::

    >>> import uri
    
    >>> args = {'foo': 'it worked'}
    >>> uri.expand_template("http://example.com/{foo}", args)
    'http://example.com/it%20worked'

    >>> args = {'a':'foo', 'b':'bar', 'a_b':'baz'}
    >>> uri.expand_template("http://example.org/{a}{b}/{a_b}", args)
    'http://example.org/foobar/baz'
    
You can also use keyword arguments for a more pythonic style::
    
    >>> uri.expand_template("http://example.org/?q={a}", a="foo")
    'http://example.org/?q=foo'
    
"""

import re
import urllib

__all__ = ["expand_template", "TemplateSyntaxError"]

class TemplateSyntaxError(Exception):
    pass

_template_pattern = re.compile(r"{([^}]+)}")

def expand_template(template, values={}, **kwargs):
    """Expand a URI template."""
    values = values.copy()
    values.update(kwargs)
    values = percent_encode(values)
    return _template_pattern.sub(lambda m: _handle_match(m, values), template)

def _handle_match(match, values):
    op, arg, variables = parse_expansion(match.group(1))
    if op:
        try:
            return getattr(_operators, op)(variables, arg, values)
        except AttributeError:
            raise TemplateSyntaxError("Unexpected operator: %r" % op)
    else:
        assert len(variables) == 1
        key, default = variables.items()[0]
        return values.get(key, default)

#
# Parse an expansion
# Adapted directly from the spec (Appendix A); extra validation has been added
# to make it pass all the tests.
#

_varname_pattern = re.compile(r"^[A-Za-z0-9]\w*$")

def parse_expansion(expansion):
    """
    Parse an expansion -- the part inside {curlybraces} -- into its component
    parts. Returns a tuple of (operator, argument, variabledict). 
    
    For example::
    
        >>> parse_expansion("-join|&|a,b,c=1")
        ('join', '&', {'a': None, 'c': '1', 'b': None})
        
        >>> parse_expansion("c=1")
        (None, None, {'c': '1'})
        
    """
    if "|" in expansion:
        (op, arg, vars_) = expansion.split("|")
        op = op[1:]
    else:
        (op, arg, vars_) = (None, None, expansion)

    vars_ = vars_.split(",")

    variables = {}
    for var in vars_:
        if "=" in var:
            (varname, vardefault) = var.split("=")
            if not vardefault:
                raise TemplateSyntaxError("Invalid variable: %r" % var)
        else:
            (varname, vardefault) = (var, None)
        
        if not _varname_pattern.match(varname):
            raise TemplateSyntaxError("Invalid variable: %r" % varname)
        variables[varname] = vardefault
        
    return (op, arg, variables)

#
# Encode an entire dictionary of values
#
def percent_encode(values):
    rv = {}
    for k, v in values.items():
        if isinstance(v, basestring):
            rv[k] = urllib.quote(v)
        else:
            rv[k] = [urllib.quote(s) for s in v]
    return rv

#
# Operators; see Section 3.3.
# Shoved into a class just so we have an ad hoc namespace.
#

class _operators(object):
    
    @staticmethod
    def opt(variables, arg, values):
        for k in variables.keys():
            v = values.get(k, None)
            if v is None or (not isinstance(v, basestring) and len(v) == 0):
                continue
            else:
                return arg
        return ""

    @staticmethod
    def neg(variables, arg, values):
        if _operators.opt(variables, arg, values):
            return ""
        else:
            return arg

    @staticmethod
    def listjoin(variables, arg, values):
        k = variables.keys()[0]
        return arg.join(values.get(k, []))

    @staticmethod
    def join(variables, arg, values):
        return arg.join([
            "%s=%s" % (k, values.get(k, default))
            for k, default in variables.items()
            if values.get(k, default) is not None
        ])

    @staticmethod
    def prefix(variables, arg, values):
        k, default = variables.items()[0]
        v = values.get(k, default)
        if v is not None and len(v) > 0:
            return arg + v
        else:
            return ""
            
    @staticmethod
    def append(variables, arg, values):
        k, default = variables.items()[0]
        v = values.get(k, default)
        if v is not None and len(v) > 0:
            return v + arg
        else:
            return ""

#
# A bunch more tests that don't rightly fit in docstrings elsewhere
# Taken from Joe Gregorio's template_parser.py.
#
_test_pre = """
    >>> expand_template('{foo}', {})
    ''
    >>> expand_template('{foo}', {'foo': 'barney'})
    'barney'
    >>> expand_template('{foo=wilma}', {})
    'wilma'
    >>> expand_template('{foo=wilma}', {'foo': 'barney'})
    'barney'
    >>> expand_template('{-prefix|&|foo}', {})
    ''
    >>> expand_template('{-prefix|&|foo=wilma}', {})
    '&wilma'
    >>> expand_template('{-prefix||foo=wilma}', {})
    'wilma'
    >>> expand_template('{-prefix|&|foo=wilma}', {'foo': 'barney'})
    '&barney'
    >>> expand_template('{-append|/|foo}', {})
    ''
    >>> expand_template('{-append|#|foo=wilma}', {})
    'wilma#'
    >>> expand_template('{-append|&?|foo=wilma}', {'foo': 'barney'})
    'barney&?'
    >>> expand_template('{-join|/|foo}', {})
    ''
    >>> expand_template('{-join|/|foo,bar}', {})
    ''
    >>> expand_template('{-join|&|q,num}', {})
    ''
    >>> expand_template('{-join|#|foo=wilma}', {})
    'foo=wilma'
    >>> expand_template('{-join|#|foo=wilma,bar}', {})
    'foo=wilma'
    >>> expand_template('{-join|&?|foo=wilma}', {'foo': 'barney'})
    'foo=barney'
    >>> expand_template('{-listjoin|/|foo}', {})
    ''
    >>> expand_template('{-listjoin|/|foo}', {'foo': ['a', 'b']})
    'a/b'
    >>> expand_template('{-listjoin||foo}', {'foo': ['a', 'b']})
    'ab'
    >>> expand_template('{-listjoin|/|foo}', {'foo': ['a']})
    'a'
    >>> expand_template('{-listjoin|/|foo}', {'foo': []})
    ''
    >>> expand_template('{-opt|&|foo}', {})
    ''
    >>> expand_template('{-opt|&|foo}', {'foo': 'fred'})
    '&'
    >>> expand_template('{-opt|&|foo}', {'foo': []})
    ''
    >>> expand_template('{-opt|&|foo}', {'foo': ['a']})
    '&'
    >>> expand_template('{-opt|&|foo,bar}', {'foo': ['a']})
    '&'
    >>> expand_template('{-opt|&|foo,bar}', {'bar': 'a'})
    '&'
    >>> expand_template('{-opt|&|foo,bar}', {})
    ''
    >>> expand_template('{-neg|&|foo}', {})
    '&'
    >>> expand_template('{-neg|&|foo}', {'foo': 'fred'})
    ''
    >>> expand_template('{-neg|&|foo}', {'foo': []})
    '&'
    >>> expand_template('{-neg|&|foo}', {'foo': ['a']})
    ''
    >>> expand_template('{-neg|&|foo,bar}', {'bar': 'a'})
    ''
    >>> expand_template('{-neg|&|foo,bar}', {'bar': []})
    '&'
    >>> expand_template('{foo}', {'foo': ' '})
    '%20'
    >>> expand_template('{-listjoin|&|foo}', {'foo': ['&', '&', '|', '_']})
    '%26&%26&%7C&_'
    
    # Extra hoops to deal with unpredictable dict ordering
    >>> expand_template('{-join|#|foo=wilma,bar=barney}', {}) in ('bar=barney#foo=wilma', 'foo=wilma#bar=barney')
    True

"""

_syntax_errors = """
    >>> expand_template("{fred=}")
    Traceback (most recent call last):
        ...
    TemplateSyntaxError: Invalid variable: 'fred='
    
    >>> expand_template("{f:}")
    Traceback (most recent call last):
        ...
    TemplateSyntaxError: Invalid variable: 'f:'
    
    >>> expand_template("{f<}")
    Traceback (most recent call last):
        ...
    TemplateSyntaxError: Invalid variable: 'f<'
    
    >>> expand_template("{<:}")
    Traceback (most recent call last):
        ...
    TemplateSyntaxError: Invalid variable: '<:'
    
    >>> expand_template("{<:fred,barney}")
    Traceback (most recent call last):
        ...
    TemplateSyntaxError: Invalid variable: '<:fred'
    
    >>> expand_template("{>:}")
    Traceback (most recent call last):
        ...
    TemplateSyntaxError: Invalid variable: '>:'
    
    >>> expand_template("{>:fred,barney}")
    Traceback (most recent call last):
        ...
    TemplateSyntaxError: Invalid variable: '>:fred'
    
"""

__test__ = {"test_pre": _test_pre, "syntax_errors": _syntax_errors}

if __name__ == '__main__':
    import doctest
    doctest.testmod()