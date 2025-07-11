from django.core.mail import EmailMultiAlternatives
from django.template import Template, Context
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class EmailService:
    @staticmethod
    def send_thank_you_email(contact, email_template):
        """
        Send a thank-you email to the contact using the provided email template.
        
        Args:
            contact: Contact instance
            email_template: EmailTemplate instance with subject and body
        """
        try:
            logger.info(f"Starting email send process for {contact.email}")
            logger.info(f"Email settings - HOST: {settings.EMAIL_HOST}, PORT: {settings.EMAIL_PORT}")
            logger.info(f"EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
            logger.info(f"EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
            
            # Create template context with contact information
            context = Context({
                'name': contact.name,
                'email': contact.email,
                'phone': contact.phone,
                'request_service': contact.get_request_service_display(),
                'request_content': contact.request_content,
                'company_name': 'EvoluSoft',
            })
            
            logger.info(f"Template context created: {dict(context.flatten())}")
            
            # Render the email subject and body with context variables
            subject_template = Template(email_template.subject)
            body_template = Template(email_template.content)
            
            rendered_subject = subject_template.render(context)
            rendered_body = body_template.render(context)
            
            logger.info(f"Rendered subject: {rendered_subject}")
            logger.info(f"Rendered body length: {len(rendered_body)} characters")
            
            # Send the email as HTML
            from django.core.mail import EmailMultiAlternatives
            
            msg = EmailMultiAlternatives(
                subject=rendered_subject,
                body=rendered_body,  # Fallback plain text
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[contact.email]
            )
            msg.attach_alternative(rendered_body, "text/html")
            
            logger.info(f"Email message created, attempting to send to {contact.email}")
            
            success = msg.send(fail_silently=False)
            
            if success:
                logger.info(f"Thank-you email sent successfully to {contact.email}")
                return True
            else:
                logger.error(f"Failed to send thank-you email to {contact.email} - send() returned {success}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending thank-you email to {contact.email}: {str(e)}")
            logger.error(f"Exception type: {type(e).__name__}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return False
    
    @staticmethod
    def get_default_thank_you_template():
        """
        Get the default thank-you email template.
        """
        from .models import EmailTemplate
        
        try:
            return EmailTemplate.objects.get(template_type='thank_you', is_active=True)
        except EmailTemplate.DoesNotExist:
            # Create default template if it doesn't exist
            return EmailTemplate.objects.create(
                name='default_thank_you',
                template_type='thank_you',
                subject='Thank you for contacting EvoluSoft!',
                content='''<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f9f9f9;">
    <div style="background: linear-gradient(135deg, #3A9285 0%, #308fb3 100%); color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0;">
        <h1 style="margin: 0; font-size: 24px;">EvoluSoft</h1>
        <p style="margin: 10px 0 0 0; opacity: 0.9;">Thank you for reaching out!</p>
    </div>
    
    <div style="background: white; padding: 30px; border-radius: 0 0 8px 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
        <p style="font-size: 16px; color: #333; margin-bottom: 20px;">Dear {{ name }},</p>
        
        <p style="font-size: 14px; color: #666; line-height: 1.6; margin-bottom: 20px;">
            Thank you for contacting <strong>{{ company_name }}</strong>! We have received your inquiry about <strong>{{ request_service }}</strong> services.
        </p>
        
        <div style="background: #f8f9fa; padding: 15px; border-radius: 6px; margin: 20px 0;">
            <p style="margin: 0; color: #333;"><strong>Your message:</strong></p>
            <p style="margin: 10px 0 0 0; color: #666; font-style: italic;">"{{ request_content }}"</p>
        </div>
        
        <p style="font-size: 14px; color: #666; line-height: 1.6; margin-bottom: 20px;">
            Our team will review your requirements and get back to you within 24-48 hours.
        </p>
        
        <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee;">
            <p style="margin: 0; color: #3A9285; font-weight: bold;">Best regards,</p>
            <p style="margin: 5px 0 0 0; color: #666;">The EvoluSoft Team</p>
        </div>
    </div>
</div>''',
                is_active=True
            )
        except EmailTemplate.MultipleObjectsReturned:
            # If multiple active templates exist, use the first one
            return EmailTemplate.objects.filter(template_type='thank_you', is_active=True).first()
