import json
from flask import request, _request_ctx_stack
from functools import wraps
from jose import jwt
from urllib.request import urlopen
import os


AUTH0_DOMAIN = os.environ.get('AUTH0_DOMAIN')
ALGORITHMS = ['RS256']
API_AUDIENCE = os.environ.get('API_AUDIENCE')

## AuthError Exception
'''
AuthError Exception
A standardized way to communicate auth failure modes
'''
class AuthError(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code


## Auth Header

'''
@TODO implement get_token_auth_header() method
    it should attempt to get the header from the request
        it should raise an AuthError if no header is present
    it should attempt to split bearer and the token
        it should raise an AuthError if the header is malformed
    return the token part of the header
'''
def get_token_auth_header():
    auth_header = request.headers.get('Authorization', None)
    if not auth_header:
        raise AuthError({
            'error': 'no authorization header',
            'description': 'Authorization header is expected'
        }, 401)

    parts = auth_header.split(' ')


    if parts[0].lower() != 'bearer':
        raise AuthError({
            'error': 'wrong authorization header type',
            'description': 'authorization header must start with \'Bearer\''
        }, 401)

    elif len(parts) == 1:
        raise AuthError({
            'error': 'invalid token',
            'description': 'token not found'
        }, 401)

    elif len(parts) > 2:
        raise AuthError({
            'error': 'invalid header',
            'description': 'authorization header must be \'Bearer\' token'
        }, 401)
    
    return parts[1]

'''
@TODO implement check_permissions(permission, payload) method
    @INPUTS
        permission: string permission (i.e. 'post:drink')
        payload: decoded jwt payload

    it should raise an AuthError if permissions are not included in the payload
        !!NOTE check your RBAC settings in Auth0
    it should raise an AuthError if the requested permission string is not in the payload permissions array
    return true otherwise
'''
def check_permissions(permission, payload):
    if 'permissions' not in payload:
        raise AuthError({
            'error': 'permissions claim not included in payload',
            'description': 'make sure that permissions claim is included in payload'
        }, 400)
    if permission not in payload['permissions']:
        raise AuthError({
            'error': 'forbidden',
            'description': 'does not have the permission for this action'
        }, 400)
    return True

'''
@TODO implement verify_decode_jwt(token) method
    @INPUTS
        token: a json web token (string)

    it should be an Auth0 token with key id (kid)
    it should verify the token using Auth0 /.well-known/jwks.json
    it should decode the payload from the token
    it should validate the claims
    return the decoded payload

    !!NOTE urlopen has a common certificate error described here: https://stackoverflow.com/questions/50236117/scraping-ssl-certificate-verify-failed-error-for-http-en-wikipedia-org
'''
def verify_decode_jwt(token):
    jwks = json.loads(urlopen(f'https://{AUTH0_DOMAIN}/.well-known/jwks.json').read())

    unverified_header = jwt.get_unverified_header(token)

    rsa_key = {}
    if 'kid' not in unverified_header:
        raise AuthError({
            'error': 'invalid token header',
            'description': 'Authorization malformed.'
        }, 401)
    
    for key in jwks['keys']:
        if key['kid'] == unverified_header['kid']:
            for claim in ['kty', 'kid', 'use', 'n', 'e']:
                rsa_key[claim] = key[claim]

    if rsa_key:
        try:
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=ALGORITHMS,
                audience=API_AUDIENCE,
                issuer=f'https://{AUTH0_DOMAIN}/'
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise AuthError({
                'error': 'token expired',
                'description': 'token expired'
            }, 401)
        except jwt.JWTClaimsError:
            raise AuthError({
                'error': 'invalid claims',
                'description': 'incorrect claims. please check the audience and issuer'
            }, 401)
        except Exception:
            raise AuthError({
                'error': 'invalid header',
                'description': 'unable to parse authentication token'
            }, 400)
    raise AuthError({
                'error': 'invalid header',
                'description': 'unable to find the appropriate key'
            }, 400)

'''
@TODO implement @requires_auth(permission) decorator method
    @INPUTS
        permission: string permission (i.e. 'post:drink')

    it should use the get_token_auth_header method to get the token
    it should use the verify_decode_jwt method to decode the jwt
    it should use the check_permissions method validate claims and check the requested permission
    return the decorator which passes the decoded payload to the decorated method
'''
def requires_auth(permission=''):
    def requires_auth_decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            token = get_token_auth_header()
            payload = verify_decode_jwt(token)
            check_permissions(permission, payload)
            return f(payload, *args, **kwargs)

        return wrapper
    return requires_auth_decorator