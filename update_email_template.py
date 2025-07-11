#!/usr/bin/env python

import os
import django

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'newsor.settings')
django.setup()

from api.models import EmailTemplate

# Get the template
template = EmailTemplate.objects.get(name='default_thank_you')

# Update with the full content
template.content = """<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f9f9f9;">
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
            <p style="margin: 10px 0 0 0; color: #666; font-style: italic;">{{ request_content }}</p>
        </div>
        
        <p style="font-size: 14px; color: #666; line-height: 1.6; margin-bottom: 20px;">
            Our team will review your requirements and get back to you within 24-48 hours.
        </p>
        
        <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee;">
            <p style="margin: 0; color: #3A9285; font-weight: bold;">Best regards,</p>
            <p style="margin: 5px 0 0 0; color: #666;">The EvoluSoft Team</p>
        </div>
    </div>
</div>"""

template.save()
print(f'Template updated successfully! New content length: {len(template.content)} characters')

# Test the updated template
from django.template import Template, Context

context = Context({
    'name': 'Test User',
    'email': 'test@example.com',
    'phone': '123456789',
    'request_service': 'Consulting',
    'request_content': 'Test message content',
    'company_name': 'EvoluSoft',
})

body_template = Template(template.content)
rendered_body = body_template.render(context)

print(f'Rendered content length: {len(rendered_body)} characters')
print('Template update completed successfully!')
