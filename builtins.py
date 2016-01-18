
def builtin(func):
    func.is_builtin = True
    return func

@builtin
def log(msg):
    print ' '.join(o.as_string() for o in msg)
    return msg