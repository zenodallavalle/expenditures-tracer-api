

class DummyRequest:
    method = 'DUMMY'


def extract_month(date):
    return f'{date.month} - {date.year}'


def extract_value(obj):
    k = 'value'
    if hasattr(obj, 'get'):
        return obj[k]
    return getattr(obj, k)


def check_precedent_money_is_valid(actual, precedent, field='date'):
    print(getattr(actual, field), getattr(precedent, field),
          (getattr(actual, field) - getattr(precedent, field)).days)
    if (getattr(actual, field) - getattr(precedent, field)).days > 31:
        return False
    return True


def extract_actual_expenditure(obj):
    k = 'actual_expenditure'
    if hasattr(obj, 'get'):
        return obj[k]
    return getattr(obj, k)


def extract_expected_expenditure(obj):
    k = 'expected_expenditure'
    if hasattr(obj, 'get'):
        return obj[k]
    return getattr(obj, k)
