from flask import Response

def base10_to_base36(num):
    """Converts a positive integer into a base36 string."""
    assert num >= 0
    digits = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'

    res = ''
    while not res or num > 0:
        num, i = divmod(num, 36)
        res = digits[i] + res
    return res

def base36_to_base10(num):
    return int(num, 36)

def custom_response(is_debug, debug_msg, prod_msg, status_code):
    if is_debug:
        print(debug_msg)
        return Response(debug_msg, status=status_code)
    else:
        print(prod_msg)
        return Response(prod_msg, status=status_code)

def print_debug_msg(is_debug, debug_msg, prod_msg):
    if is_debug:
        print(debug_msg)
    else:
        print(prod_msg)

def batch_generator(data, batch_size):
    for i in range(0, len(data), batch_size):
        if i+batch_size > len(data):
            yield data[i:]
        else:
            yield data[i:i+batch_size]

