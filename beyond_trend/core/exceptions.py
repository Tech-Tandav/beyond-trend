from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.exceptions import APIException


class NoContent(APIException):
    status_code = status.HTTP_204_NO_CONTENT
    default_detail = _('Content temporarily unavailable, try again later.')
    default_code = 'no_content'


class NotFound(APIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = _('This specific data is not present .')
    default_code = 'not_found'
    
    
class BadRequest(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _('Bad Request')
    default_code = 'bad_request'


class ServiceUnavailable(APIException):
    status_code = 503
    default_detail = 'Service temporarily unavailable, try again later.'
    default_code = 'service_unavailable'
    

class SlackSendFailed(Exception):
    pass
