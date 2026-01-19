"""Custom middleware for Novel Web application."""


class NoCacheMiddleware:
    """
    Middleware to prevent browser caching of HTML pages.
    This ensures that template updates are immediately visible without hard refresh.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Only apply no-cache headers to HTML responses
        if response.get('Content-Type', '').startswith('text/html'):
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'

        return response
