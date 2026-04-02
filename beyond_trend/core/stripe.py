import stripe, logging
from django.conf import settings
from datetime import date, timedelta
from django.utils import timezone
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView 
from django.shortcuts import get_object_or_404
from car_rental.rental.models import  Payment
from rest_framework.response import Response  
from rest_framework import status
from car_rental.core.serializers import PaymentSessionSerializer
from django.http import JsonResponse
from rest_framework.exceptions import APIException
from car_rental.rental.models import Rental

stripe.api_key = settings.STRIPE_SECRET_KEY 

   
class CreateCheckoutSessionView(APIView):

    def post(self, request, *args, **kwargs):
        serializer = PaymentSessionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        rental_obj = get_object_or_404(Rental, id=data.get('rental_id'))
        try:
            # Define line item based on price_id or amount
            if data.get('price_id'):
                line_item = {
                    'price': data['price_id'],
                    'quantity': data['quantity'],
                }
            else:
                # One-time payment with custom amount
                
                base_price = int(rental_obj.final_price)  # Assuming final_price is in cents
                line_item = {
                    'price_data': {
                        'currency': data['currency'],
                        'product_data': {
                            'name': 'Rental Payment',
                        },
                        'unit_amount': base_price,  # Amount in cents
                    },
                    'quantity': 1,
                }

            # Create Stripe Checkout Session
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[line_item],
                mode='payment',
                success_url=data['success_url'],
                cancel_url=data['cancel_url'],
                metadata={
                    'user_id': request.user.id if request.user.is_authenticated else None,
                    # Add other metadata as needed
                }
            )

            # Save payment record to database
            Payment.objects.create(
                user=request.user if request.user.is_authenticated else None,
                stripe_session_id=checkout_session.id,
                # amount=data.get('amount', 0),
                currency=data.get('currency', 'aud'),
                status='pending',
                rental=rental_obj  # Assuming rental_id is passed in the request data
            )

            return Response({
                'session_id': checkout_session.id,
                'session_url': checkout_session.url
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            raise APIException(f"{e}")





logger = logging.getLogger(__name__)

@csrf_exempt
def stripe_webhook(request):
    """Handle Stripe webhook events."""
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    print("Received Stripe webhook event")
    try:
        # Construct the event using the payload and signature
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        # Invalid payload
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return HttpResponse(status=400)

    # Handle the event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        handle_successful_payment(session)

    # ... handle other event types (e.g., payment_intent.succeeded, payment_intent.payment_failed)

    return JsonResponse({'status': 'success'}, status=200)


def handle_successful_payment(session):
    """
    Update your database and perform post-payment actions.
    """
    session_id = session['id']
    payment_intent_id = session.get('payment_intent')

    try:
        payment = Payment.objects.get(stripe_session_id=session_id)
        print(payment)
        print(f"Updating payment record for session {session_id}")
        payment.status = 'succeeded'
        payment.stripe_payment_intent_id = payment_intent_id
        payment.save()

        # TODO: Trigger any post-payment logic here
        # e.g., grant access to content, send confirmation email [citation:7]
        logger.info(f"Payment succeeded for session {session_id}")

    except Payment.DoesNotExist:
        logger.error(f"Payment record not found for session {session_id}")