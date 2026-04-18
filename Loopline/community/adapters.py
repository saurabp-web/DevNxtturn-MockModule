from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.conf import settings
from django.contrib.auth import get_user_model
from allauth.account.models import EmailAddress


class NxtTurnAccountAdapter(DefaultAccountAdapter):
    def get_site_domain(self):
        return (
            settings.FRONTEND_URL.replace("https://", "")
            .replace("http://", "")
            .strip("/")
        )

    def get_email_confirmation_url(self, request, emailconfirmation):
        return f"{settings.FRONTEND_URL}/verify-email/{emailconfirmation.key}"

    def send_mail(self, template_prefix, email, context):
        """
        GOD MODE v2: Not only fixes the domain, but also fixes the PATH
        to match the Vue Router exactly.
        """
        context["protocol"] = "https"
        context["domain"] = self.get_site_domain()

        # If this is a password reset email, we have 'uid' and 'token' in the context
        if "password_reset_url" in context:
            uid = context.get("uid")
            token = context.get("token")
            # We force the path to match your Vue route: /auth/reset-password/uid/token/
            context["password_reset_url"] = (
                f"{settings.FRONTEND_URL}/auth/reset-password/{uid}/{token}/"
            )

        return super().send_mail(template_prefix, email, context)

    def format_email_subject(self, subject):
        return f"nxtturn - {subject}"


class NxtTurnSocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        if sociallogin.is_existing:
            return

        email = sociallogin.user.email or sociallogin.account.extra_data.get("email")
        if email:
            User = get_user_model()
            try:
                user = User.objects.get(email__iexact=email)
                # Link the account in the DB
                sociallogin.connect(request, user)

                # FORCE the user onto every attribute to prevent 500 errors
                sociallogin.user = user
                sociallogin.account.user = user  # This satisfies the ORM
            except User.DoesNotExist:
                pass
