from common import utils


def welcome_email(username, email, request):
    utils.send_html_mail(
        subject='Welcome to our community!',
        recipient_list=[email],
        html_content=f"""
        <html>
            <head></head>
          <body>
            <p>
               Congratulation {username}, the registration was successful. Go visit our market!<br> 
               <a href="http://{request.get_host()}/market">Click here</a>
            </p>
          </body>
        </html>
        """,
        fail_silently=True
    )