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
