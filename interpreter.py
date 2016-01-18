
from jsobject import *
import builtins

class NameSpace(object):
    def __init__(self, parent=None, root=False):
        self.locals = {}
        self.parent = parent
        self.root = root

    def declare_var(self, name):
        self.locals[name] = None

    def assign_value(self, name, value):
        if name in self.locals or self.root:
            self.locals[name] = value
        else:
            self.parent.assign_value(name, value)

    def get_value(self, name):
        if name in self.locals:
            return self.locals[name]
        elif self.root:
            return Undefined()
        else:
            return self.parent.get_value(name)

    def get_parent(self):
        if self.root:
            return self
        else:
            return self.parent

    def nest(self):
        return NameSpace(self)


class Interpreter(object):

    def __init__(self):
        self.stack = []
        self.call_stack = []
        self.instruction_pointer = 0
        self.namespace = NameSpace(root=True)
        self._namespaces = []
        self.params = []
        self.running = True

        self.create_builtins()

    def wrap_namespace(self):
        self.namespace = self.namespace.nest()

    def unwrap_namespace(self):
        self.namespace = self.namespace.get_parent()

    def push_namespace(self, namespace):
        self._namespaces.append(self.namespace)
        self.namespace = namespace

    def pop_namespace(self):
        self.namespace = self._namespaces.pop()
        return self.namespace

    def declare(self, name):
        self.namespace.declare_var(name)

    def load_const(self, value):
        self.stack.append(value)

    def load_var(self, name):
        self.stack.append(
            self.namespace.get_value(name)
        )

    def store(self, name):
        value = self.stack[-1]
        self.namespace.assign_value(name, value)

    def calc_binary(self, op):
        method = {
            'PLUS': lambda a,b: a.add(b),
            'MINUS': lambda a,b: a.minus(b),
            'MUL': lambda a,b: a.mul(b),
            'DIV': lambda a,b: a.div(b),
            'MOD': lambda a,b: a.mod(b)
        }
        b = self.stack.pop()
        a = self.stack.pop()

        self.stack.append(
            method[op](a, b)
        )

    def jump(self, n):
        self.instruction_pointer += n

    def jump_on_false(self, n):
        a = self.stack.pop()

        if not a.as_bool():
            self.jump(n)

    def param(self, name):
        self.params.append(name)

    def new_func(self, name):
        params = [s.value for s in self.stack.pop().value]

        f = Function(params=params, address=self.instruction_pointer + 1,
            namespace=self.namespace.nest())

        self.stack.append(f)

        if name:
            self.store(name)

    def call(self, _):
        func = self.stack.pop()

        if func.is_builtin:
            self.call_builtin(func)

        else:
            self.call_js(func)

    def call_builtin(self, func):
        args = self.stack.pop().value
        self.stack.append(func(args))

    def call_js(self, func):
        self.call_stack.append(self.instruction_pointer)

        self.push_namespace(func.namespace)

        for i, param in enumerate(self.stack.pop().value):
        # for i, param in enumerate(self.stack.pop().value):
            self.namespace.locals[func.params[i]] = param

        self.instruction_pointer = func.address

    def return_(self, _):
        self.pop_namespace()
        self.instruction_pointer = self.call_stack.pop()


    def create_array(self, size=0):
        array = Array(size)
        for _ in xrange(size):
            # if self.stack:
                array.add_value(self.stack.pop())
            # else:
                # break

        self.stack.append(array)


    def comp(self, op):
        b = self.stack.pop()
        a = self.stack.pop()
        method = {
            'LT': lambda a,b: a.lt(b),
            'LE': lambda a,b: a.le(b),
            'EQ': lambda a,b: a.eq(b)
        }
        self.stack.append(method[op](a,b))

    def pop_stack(self, op):
        self.stack.pop()

    def end(self, op):
        self.running = False

    def execute(self, opcodes):
        map = {
            'DECLARE': self.declare,
            'LOAD_CONST': self.load_const,
            'STORE': self.store,
            'LOAD_VAR': self.load_var,
            'CALC_BINARY': self.calc_binary,
            'JUMP_ON_FALSE': self.jump_on_false,
            'JUMP': self.jump,
            # 'PARAM': self.param,
            'CALL': self.call,
            'NEW_FUNC': self.new_func,
            'CREATE_ARRAY': self.create_array,
            'RETURN': self.return_,
            'COMP': self.comp,
            'POP_STACK': self.pop_stack,
            'END': self.end
        }

        try:

            # while self.instruction_pointer < len(opcodes):
            while self.running:
                code, value = opcodes[self.instruction_pointer]
                map[code](value)

                self.instruction_pointer += 1

        except IndexError:
            print opcodes[self.instruction_pointer], self.instruction_pointer
            raise


    def create_builtins(self):
        self.namespace.assign_value('log', builtins.log)