from datetime import datetime
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from urllib import parse

RESERVED_QUERYSTRING_KEYS = [
    'month',
]


def parseQueryString(get_response):
    def middleware(request):
        # Thing executed before
        qs = parse.parse_qs(request.META['QUERY_STRING'])
        request.params = qs
        response = get_response(request)
        # Thing executed after next middleware
        return response

    return middleware


def _analyze_request_month(request):
    month = request.params.get('month', [request.headers.get('month', None)])[0]
    if month:
        month, year = [int(x.strip()) for x in month.split('-')[:2]]
    else:
        n = datetime.now()
        month = n.month
        year = n.year
    min_date = datetime(year, month, 1)
    max_date = min_date + relativedelta(months=1)
    request.min_date = timezone.make_aware(min_date)
    request.max_date = timezone.make_aware(max_date)
    return request


def parseMonth(get_response):
    def middleware(request):
        # Thing executed before
        request = _analyze_request_month(request)
        response = get_response(request)
        # Thing executed after next middleware
        return response

    return middleware
