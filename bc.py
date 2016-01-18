import operator

import jsobject as jsType

from jsparser import parse, opTypeNames as assignOpMap, assignOps, tokens, Node


class ExpressionGenerator(object):

    def __call__(self, node):
        return getattr(self, node.type)(node)

    def _binary_op(self, node, bc):
        return (
            self(node[0])
            + self(node[1])
            + [bc]
        )


    def IDENTIFIER(self, node):
        return [('LOAD_VAR', node.value)]


    def PLUS(self, node):
        return self._binary_op(node, ('CALC_BINARY', node.type))

    MINUS = MUL = DIV = MOD = PLUS


    def GROUP(self, node):
        return self(node[0])


    def AND(self, node):
        return self._binary_op(node, ('BOOL_OP', node.type))

    OR = AND


    def EQ(self, node):
        return self._binary_op(node, ('COMP', node.type))

    NE = STRICT_EQ = STRICT_NE = LT = LE = GT = GE = EQ


    #constants

    def NUMBER(self, node):
        return [('LOAD_CONST', jsType.Number(node.value))]

    def TRUE(self, node):
        return [('LOAD_CONST', jsType.Boolean(True))]

    def FALSE(self, node):
        return [('LOAD_CONST', jsType.Boolean(False))]

    def INCREMENT(self, node):
        postfix = getattr(node, 'postfix', False)
        return [
            ('LOAD_VAR', node[0].value),
            ('LOAD_CONST', jsType.Integer(1)),
            ('CALC_BINARY', 'PLUS'),
            ('STORE', node[0].value)
        ]


    def ARRAY_INIT(self, node):
        if len(node) > 0:
            bc = reduce(operator.add, map(self, node[::-1]))
        else:
            bc = []
        return bc + [('CREATE_ARRAY', len(node))]

    LIST = ARRAY_INIT

    def PROPERTY_INIT(self, node):
        key = node[0]

    def OBJECT_INIT(self, node):
        print node

    def FUNCTION(self, node):
        bc = []

        params = node.params
        for param in params[::-1]:
            bc.append(('LOAD_CONST', jsType.String(param)))
        bc.append(('CREATE_ARRAY', len(params)))

        bc.append(('NEW_FUNC', getattr(node, 'name', None)))

        bcg = BytecodeGenerator()

        body = bcg(node.body)        

        if not body or body[-1][0] != 'RETURN':
            body.extend([
                ('LOAD_CONST', jsType.Undefined()),
                ('RETURN', None)
            ])

        bc.append(('JUMP', len(body)))
        bc.extend(body)

        return bc


    def ASSIGN(self, node):

        name = node[0].value

        #get right side
        bc = self(node[1])

        #is += etc.?
        if node[0].assignOp:
            op = assignOpMap[tokens[node[0].assignOp]]
            bc = [('LOAD_VAR', name)] + bc + [('CALC_BINARY', op)]

        return bc + [('STORE', name)]

    def CALL(self, node):
        return (
            self(node[1])
            + self(node[0])
            + [('CALL', None )]
        )
    

class ConditionGenerator(object):
    def __init__(self):
        self._expression = ExpressionGenerator()
    
    def IF(self, node):
        bc = self._expression(node.condition)

        then = to_bytecode(node.thenPart)
        else_ = self.ELSE(node.elsePart)

        #1 for jump instruction of then block
        bc.append(('JUMP_ON_FALSE', len(then)+1) )
        bc.extend(then)
        bc.append(('JUMP', len(else_)))
        bc.extend(else_)

        return bc

    def ELSE(self, node):
        if node is None:
            return []
        elif node.type == 'BLOCK':
            return to_bytecode(node)
        elif node.type == 'IF':
            return self.IF(node)

class BytecodeGenerator(object):
    def __init__(self, main=False):
        self.bytecode = []
        self._expression = ExpressionGenerator()
        self.main = main
        self.clean = False
        self._condition = ConditionGenerator()


    def expression(self, node):
        bc = self._expression(node)
        self.bytecode.extend(bc)

    def var(self, node):
        self.bytecode.append(('DECLARE', node.name))

        if hasattr(node, 'initializer'):
            self.bytecode.extend(
                self._expression(node.initializer)
                )
            self.bytecode.append(('STORE', node.name))
        else:
            self.clean = True

    def return_(self, node):
        if isinstance(node.value, Node):
            self.bytecode.extend(self._expression(node.value))
        else:
            self.bytecode.append(('LOAD_CONST', jsType.Undefined()))

        self.bytecode.append(('RETURN', None))


    def if_(self, node):
        self.bytecode.extend(self._condition.IF(node))

    def while_(self, node):
        body = to_bytecode(node.body)
        
        bc = self._expression(node.condition)
        bc.append(('JUMP_ON_FALSE', len(body)+1) )  

        for i, code in enumerate(body):
            if code[0] == 'CONTINUE' and code[1] is None:
                body[i] = ('JUMP', -(i+len(bc)+1))

            elif code[0] == 'BREAK':
                body[i] = ('JUMP', len(body)-i)

        #make it a loop
        body.append(('JUMP', -(len(body)+len(bc)+1)))

        bc.extend(body)

        self.bytecode.extend(bc)
    
    def for_(self, node):
        setup = []
        if node.setup:
            setup = to_bytecode([node.setup])

        condition = self._expression(node.condition)        
        
        body = to_bytecode(node.body)
        update = self._expression(node.update)        

        condition.append(('JUMP_ON_FALSE',
            len(body)+len(update)+1) )  

        for i, code in enumerate(body):
            if code[0] == 'CONTINUE' and code[1] is None:
                body[i] = ('JUMP', len(body)-i-1)

            elif code[0] == 'BREAK':
                body[i] = ('JUMP', len(body)+len(update)-i)

        body.extend(update)
        #make it a loop
        body.append(('JUMP', -(len(body)+len(condition)+1)))

        self.bytecode.extend(setup + condition + body)

    def continue_(self, node):
        self.bytecode.append(('CONTINUE', None))

    def break_(self, node):
        self.bytecode.append(('BREAK', None))
    
    def __call__(self, nodes):
        for node in nodes:
            self.clean = False
            if node.type == 'SEMICOLON':
                self.expression(node.expression)

            elif node.type == 'VAR':
                map(self.var, node)
           
            elif node.type in {'FUNCTION'}:
                self.expression(node)
           
            elif node.type == 'RETURN':
                self.return_(node)
                self.clean = True

            elif node.type == 'WHILE':
                self.while_(node)
                self.clean = True

            elif node.type == 'FOR':
                self.for_(node)
                self.clean = True

            elif node.type == 'IF':
                self.if_(node)
                self.clean = True
            elif node.type == 'CONTINUE':
                self.continue_(node)
                self.clean = True
            elif node.type == 'BREAK':
                self.break_(node)
                self.clean = True
            # else:
            #     print 'x', node


            if not self.clean:
                self.bytecode.append(('POP_STACK', None))

        if self.main:
            self.bytecode.append(('END', None))
        
        return self.bytecode


to_bytecode = lambda xs: BytecodeGenerator()(xs)

if __name__ == '__main__':
    from pprint import pprint

    with open('example.js') as fobj:
        instructions = parse(fobj.read())

    bcg = BytecodeGenerator(True)

    bytecode = bcg(instructions)
    # pprint(bytecode)

    from interpreter import Interpreter
    ip = Interpreter()
    ip.execute(bytecode)

    # print 'locals', ip.namespace.locals