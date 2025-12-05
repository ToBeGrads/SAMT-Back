import jwt
from django.conf import settings
from django.http import JsonResponse

class JWTAuthenticationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Exempt paths that don't need JWT authentication
        exempt_paths = [
            '/Login/', 
            '/SignUp/', 
            '/media/', 
            '/admin',  # Changed from '/admin/' to match all admin paths
            '/static/',
            '/favicon.ico',
            '/.well-known/'
        ]
        
        # Check if request path starts with any exempt path
        is_exempt = any(request.path.startswith(path) for path in exempt_paths)
        
        if is_exempt:
            return self.get_response(request)
        
        # For non-exempt paths, check for JWT token
        auth_header = request.headers.get('Authorization')
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
            return JsonResponse({
                "message": "Auth header is required!"
            }, status=400)

        response = self.get_response(request)
        return response