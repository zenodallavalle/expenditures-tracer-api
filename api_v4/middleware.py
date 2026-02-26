from datetime import datetime
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from urllib import parse

RESERVED_QUERYSTRING_KEYS = [
    "month",
]


def parseQueryString(get_response):
    def middleware(request):
        # Thing executed before
        qs = parse.parse_qs(request.META["QUERY_STRING"])
        request.params = qs
        response = get_response(request)
        # Thing executed after next middleware
        return response

    return middleware


def _analyze_request_month(request):
    month = request.params.get(
        "month", [request.headers.get("month", datetime.now().strftime("%m-%Y"))]
    )[0]
    min_date = datetime.strptime(month, "%m-%Y")
    max_date = min_date + relativedelta(months=1)
    request.min_date = timezone.make_aware(min_date)
    request.max_date = timezone.make_aware(max_date)
    return request


def _analyze_month_list_boundaries(request):
    month_list_gte = request.params.get("month_list_gte", [None])[0]
    month_list_lt = request.params.get("month_list_lte", [None])[0]
    if month_list_gte is None or month_list_lt is None:
        request_month_list_lte = request.max_date
        request_month_list_gte = request.min_date - relativedelta(months=12)
    else:
        min_date = datetime.strptime(month_list_gte, "%m-%Y")
        max_date = datetime.strptime(month_list_lt, "%m-%Y")
        request_month_list_gte = timezone.make_aware(min_date)
        request_month_list_lte = timezone.make_aware(max_date)
    request.request_month_list_gte = request_month_list_gte
    request.request_month_list_lte = request_month_list_lte
    return request


def parseMonth(get_response):
    def middleware(request):
        # Thing executed before
        request = _analyze_request_month(request)
        request = _analyze_month_list_boundaries(request)
        response = get_response(request)
        # Thing executed after next middleware
        return response

    return middleware
