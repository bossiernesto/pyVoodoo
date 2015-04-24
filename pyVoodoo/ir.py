

def with_name(f, name):
    try:
        f.__name__=name
        return f
    except (TypeError,AttributeError):
        return function(
            f.func_code, f.func_globals, name, f.func_defaults, f.func_closure
        )