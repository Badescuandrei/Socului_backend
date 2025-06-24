from djoser import email
from django.contrib.auth.tokens import default_token_generator
from djoser import utils
from djoser.conf import settings as djoser_settings


class ActivationEmail(email.ActivationEmail):
    template_name = 'email/activation_email.html'
    
    def get_context_data(self):
        # Get the default context first
        context = super().get_context_data()
        
        # Get user from context
        user = context.get("user")
        
        # Generate uid and token manually
        uid = utils.encode_uid(user.pk)
        token = default_token_generator.make_token(user)
        
        # Override with our custom deep link URL
        context["uid"] = uid
        context["token"] = token
        context["activation_url"] = f"https://badescu.design/activate/{uid}/{token}"
        
        
        return context