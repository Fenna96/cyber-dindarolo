"""
UTILITY FUNCTIONS FOR ALL APPS
"""
from django.core.mail import send_mail
from django.http import HttpRequest

from manager import models
import threading
from threading import Thread

from martistupe.settings import EMAIL_HOST_USER


def group_by_key(values, keys, grouped_by, desc=None):
    groups = []
    # if desc option, reverse is activated. Therefore you have ordered in descending order
    keys = sorted(keys, reverse=desc)

    # for each unique key, create a group list with that key
    for key in keys:
        new_dict = {}
        new_dict["key"] = key
        new_dict["group"] = []
        for record in values:
            # add value if key correspond
            if getattr(record, grouped_by) == key:
                new_dict["group"].append(record)
        groups.append(new_dict)
    return groups


def get_balance(request: HttpRequest):
    if user := request.user:
        try:
            balance = models.Balance.objects.get(user=user)
        except models.Balance.DoesNotExist:
            balance = models.Balance(user=user, balance=0)
            balance.save()
        return balance


class EmailThread(threading.Thread):
    def __init__(self, subject, html_content, recipient_list, fail_silently):
        self.subject = subject
        self.recipient_list = recipient_list
        self.html_content = html_content
        self.fail_silently = fail_silently
        threading.Thread.__init__(self)

    def run(self):
        send_mail(
            subject=self.subject,
            message="",
            from_email=EMAIL_HOST_USER,
            recipient_list=self.recipient_list,
            html_message=self.html_content,
            fail_silently=self.fail_silently,
        )


# Function to send async emails
def send_html_mail(subject, html_content, recipient_list, fail_silently):
    EmailThread(subject, html_content, recipient_list, fail_silently).start()
