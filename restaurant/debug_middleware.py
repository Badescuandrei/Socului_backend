class RequestDebugMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # --- Code executed on an incoming request, BEFORE the view is called ---

        if 'activation' in request.path:
            print("\n--- DEBUG MIDDLEWARE: INCOMING REQUEST ---")
            print(f"PATH: {request.path}")
            print(f"METHOD: {request.method}")
            print(f"HEADERS: {request.headers}")
            print("----------------------------------------\n")

        # Let the request continue to the next middleware and the view
        response = self.get_response(request)

        # --- Code executed on the outgoing response, AFTER the view is called ---

        if 'activation' in request.path:
            print("\n--- DEBUG MIDDLEWARE: OUTGOING RESPONSE ---")
            print(f"STATUS CODE: {response.status_code}")
            print(f"RESPONSE HEADERS: {response.headers}")
            # We can try to see the content, but it might be empty on 403
            try:
                print(f"RESPONSE CONTENT: {response.content}")
            except Exception:
                print("RESPONSE CONTENT: Not available or already streamed.")
            print("-----------------------------------------\n")

        return response