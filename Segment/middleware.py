import jwt
from django.conf import settings
from django.http import JsonResponse

class JWTAuthenticationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        exempt_paths = ['/Login/', '/SignUp/', '/media/']
        # If request path is in exempt list, skip authentication
        if request.path in exempt_paths or request.path.startswith('/media/'):
            return self.get_response(request)
        
        auth_header = request.headers.get('Authorization')
        # print(auth_header)
        token = None
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1] 
        if token:
            try:
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
                request.doc_id = payload['id']
            except jwt.ExpiredSignatureError:
                return JsonResponse({'message': 'Token expired'}, status=401)
            except jwt.InvalidTokenError:
                return JsonResponse({'message': 'Invalid token'}, status=401)
        else:
            request.doc_id = 1
            return JsonResponse({
                "message" : "Auth header is required !"
                }, status = 400)

        response = self.get_response(request)
        return response
