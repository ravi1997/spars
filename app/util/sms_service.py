


from flask import current_app as app
import requests

def send_sms(mobile,message):
	# Data for the POST request

	data = {
		'username': app.config.get('OTP_USERNAME'),
		'password': app.config.get('OTP_PASSWORD'),
		'senderid': app.config.get('OTP_SENDERID'),
		'mobileNos': mobile,
		'message': f'{message}',
		'templateid1': app.config.get('OTP_ID')
	}

	# Headers for the POST request
	headers = {
		'Content-Type': 'application/x-www-form-urlencoded'
	}

	# URL of the service
	url = app.config.get("OTP_SERVER")
	app.logger.info(url)
	app.logger.info(f'username : {app.config.get("OTP_USERNAME")}')
	app.logger.info(f'password : {app.config.get("OTP_PASSWORD")}')
	app.logger.info(f'senderid : {app.config.get("OTP_SENDERID")}')
	app.logger.info(f'templateid1 : {app.config.get("OTP_ID")}')

	# Send the POST request
	response = requests.post(url, data=data, headers=headers)

	# Return the response from the SMS service
	return response.status_code


def send_otp(mobile, otp_value):
    """ Placeholder function to send OTP via SMS or Email """
    # If you want to use email:
    msg = f"Your OTP is {otp_value}"
    app.logger.info(msg)
    # If you want to use SMS, you can integrate with Twilio or any other SMS API
    # send_sms(user.mobile, otp_value)
    return send_sms(mobile, msg)
