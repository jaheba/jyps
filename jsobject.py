
class BoxedValue(object):
    def __init__(self, value):
        self.value = value

        if hasattr(self, 'convert'):
            self.value = self.convert(self.value)

class Boolean(BoxedValue):
    def __repr__(self):
        return '<B %s>' %self.value

    def as_bool(self):
        return self.value

class Undefined(BoxedValue):
    def __init__(self, value=None):
        BoxedValue.__init__(self, None)

    def as_bool(self):
        return False


class Float(BoxedValue):
    convert = float

    def as_string(self):
        return str(self.value)

    def as_bool(self):
        return Boolean(self.value != 0)

    def add(self, other):
        return other.add_float(self)

    def add_integer(self, other):
        return Float(self.value + other.value)

    def add_string(self, other):
        return other.ladd_float(self)


    def mul(self, other):
        return other.mul_float(self)

    def mul_float(self, other):
        return self.value * other.value

class Integer(BoxedValue):
    convert = int

    def as_string(self):
        return str(self.value)

    def as_bool(self):
        return Boolean(self.value != 0)

    def add(self, other):
        return other.add_integer(self)

    def add_integer(self, other):
        return Integer(self.value + other.value)

    def add_string(self, other):
        return other.ladd_integer(self)


    def mul(self, other):
        return other.mul_integer(self)

    def mul_integer(self, other):
        return Integer(self.value * other.value)

    def minus(self, other):
        return other.lminus_integer(self)

    def minus_integer(self, other):
        return Integer(self.value * other.value)
    
    def lminus_integer(self, other):
        return Integer(other.value - self.value)

    def mod(self, other):
        return other.lmod_integer(self)

    def lmod_integer(self, other):
        return other.mod_integer(self)

    def mod_integer(self, other):
        return Integer(self.value%other.value)

    def lt(self, other):
        return Boolean(self.value < other.value)

    def eq(self, other):
        return Boolean(self.value == other.value)
    
    def le(self, other):
        return Boolean(self.value <= other.value)

    def __repr__(self):
        return "<I %s>" %self.value

Number = Integer

class String(BoxedValue):

    def as_string(self):
        return self

    def as_bool(self):
        return Boolean(len(self.value) != 0)

    def add(self, other):
        return other.add_string(self)

    def add_other(self, other):
        return String(other.as_string() + self.value)

    def ladd_other(self, other):
        return String(self.value + other.as_string())

    
    add_integer = add_other
    ladd_integer = ladd_other

    add_float = add_other
    ladd_float = ladd_other

    def __repr__(self):
        return '<S %s>' %self.value

class JSObject(BoxedValue):
    def __init__(self):
        self.dict = dict()

    def as_string(self):
        return "[object Object]"

    def add_key_value(self, key, value):
        self.dict[key.as_string()] = value

    def get_value(self, key):
        return self.dict[key.as_string()]



class Array(BoxedValue):
    def __init__(self, value):
        self.value = []

    def add_value(self, value):
        self.value.append(value)


class Function(BoxedValue):
    def __init__(self, address, params, namespace):
        self.address = address
        self.params = params
        self.namespace = namespace
        self.is_builtin = False

    def call(self):
        pass

# a = Integer(1)
# b = String("2")

# print a.add(b)
# print b.add(a).add(Float(2.3))

# print String("").as_bool()
# print String("x").as_bool()