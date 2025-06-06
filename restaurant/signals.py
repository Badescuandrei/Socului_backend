import requests
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.conf import settings
from .models import Order, UserProfile
from django.contrib.auth.models import User

@receiver(pre_save, sender=Order)
def store_previous_order_status(sender, instance, **kwargs):
    if instance.pk:
        try:
            instance._previous_status = Order.objects.get(pk=instance.pk).status
        except Order.DoesNotExist:
            instance._previous_status = None
    else:
        instance._previous_status = None

@receiver(post_save, sender=Order)
def order_status_changed(sender, instance, created, **kwargs):
    # Check if the status has changed to 'Delivering' (status code 1)
    # and it was not 'Delivering' before (or it's a new order set to 'Delivering')
    if instance.status == 1 and (created or instance._previous_status != 1):
        if instance.is_voice_order:
            customer_name = instance.customer_name
            phone_number = instance.customer_phone
        elif instance.user:
            # Assuming you have a way to get the user's phone number.
            # If User model has a 'phone_number' field:
            # phone_number = instance.user.phone_number 
            # If you have a profile model linked to User with phone:
            # phone_number = instance.user.profile.phone_number
            # For now, as a placeholder, let's use a default or leave it blank
            # if the direct phone number isn't on the User model.
            # This needs to be adjusted based on your actual User model structure.
            customer_name = instance.user.get_full_name() or instance.user.username
            
            # Placeholder for phone number - you'll need to adjust this
            # based on how you store user phone numbers.
            # For the example, I'll try to get it from a potential 'profile' or a direct field.
            # This is a common pattern, but might not match your exact setup.
            phone_number = None
            if hasattr(instance.user, 'userprofile') and instance.user.userprofile:
                 phone_number = instance.user.userprofile.phone_number

            # If still no phone number, and you require it for Twilio,
            # you might need to log this or handle it.
            # For demonstration, we'll proceed if we have a name,
            # but Twilio will fail without a valid phone number.
            if not phone_number:
                print(f"Warning: Phone number not found for user {customer_name} for order {instance.pk}")
                # Depending on requirements, you might want to return here if phone is mandatory
                # return 
        else:
            # This case should ideally not happen if an order always has a user or is a voice order
            print(f"Warning: Order {instance.pk} has no user and is not a voice order. Cannot send SMS.")
            return

        if not phone_number:
            print(f"Critical: No phone number for order {instance.pk} to send SMS. Name: {customer_name}")
            return # Cannot send SMS without a phone number

        payload = [
            {
                "name": customer_name,
                "phone_number": phone_number
            }
        ]
        
        webhook_url = getattr(settings, 'N8N_WEBHOOK_URL', None)
        if webhook_url:
            try:
                print(f"Sending webhook for order {instance.pk} to {webhook_url} with payload: {payload}")
                response = requests.post(webhook_url, json=payload, timeout=10)
                response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)
                print(f"Webhook for order {instance.pk} sent successfully. Status: {response.status_code}")
            except requests.exceptions.RequestException as e:
                print(f"Error sending webhook for order {instance.pk}: {e}")
        else:
            print("N8N_WEBHOOK_URL not configured in settings.") 

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
    else:
        UserProfile.objects.get_or_create(user=instance) 