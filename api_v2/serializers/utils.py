from dateutil import relativedelta


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
    actual_date = getattr(actual, field)
    precedent_date = getattr(precedent, field)
    if (actual_date - relativedelta.relativedelta(months=1)) > precedent_date:
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
