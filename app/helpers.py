def is_number(x):
    try:
        float(x)
        return True
    except ValueError:
        return False