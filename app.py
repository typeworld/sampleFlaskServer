# Import Flask web server
from flask import Flask, Response, request, redirect, session as flaskSession, abort, g
global app
app = Flask(__name__)

# Import typeworld module
import typeworld

# Import JSON module
import json

# Main API Endpoint URL
# For security reasons (so that URLs don’t show up in server logs anywhere),
# we’re only allowing POST requests, where data is transmitted hidden in the requests’ HTTP headers
@app.route('/api', methods=['POST'])
def api():

	# SECURITY WARNING:
	# Please note that it’s your responsibility to quarantine all incoming data against SQL injections attacks etc.

	# Only the `commands` parameter is required at this point. All other parameters are optional until we
	# deal with the respective commands, where they will be checked for being present.

	# API Commands (required)
	# Comma-separated list of commands such as "installFonts,installableFonts".
	# It is critical that they are executed in the order defined in this incoming parameter.
	# See: https://github.com/typeworld/typeworld/tree/master/Lib/typeworld/api#user-content-class-rootresponse
	commands = request.values.get('commands')

	# `commands` is a required parameter. If it’s missing, return the request immediately with 404 Not Found
	# All valid requests must carry `commands`. If they don’t, they are probably not coming from the Type.World App.
	# You can use this as a cheap first step to to sort valid from invalid traffic
	if not commands:
		return abort(404)

	# Otherwise, parse commands into list:
	commandsList = commands.split(',')

	# Subscription ID
	# String identifying a subscription on your server.
	# For example, the user account of your commercial font customer
	# could be identified by an anonymous ID pointint to that user account.
	# You have made the `subscriptionID` known to the Type.World app as part of the subscription URL.
	# See: https://type.world/developer#the-subscription-url
	subscriptionID = request.values.get('subscriptionID')

	# Secret Key
	# String as a secret key to a subscription on your server.
	# You have made the `secretKey` known to the Type.World app as part of the subscription URL.
	# See: https://type.world/developer#the-subscription-url
	# And: https://type.world/developer#security-levels
	secretKey = request.values.get('secretKey')

	# Access Token
	# Single-use access token to identify that users are accessing this link from inside your website’s user account.
	# You have made the `accessToken` known to the Type.World app as part of the subscription URL.
	# See: https://type.world/developer#the-subscription-url
	# And: https://type.world/developer#security-levels
	accessToken = request.values.get('accessToken')

	# Fonts
	# Comma-separated list of `fontID`s to install or uninstall
	fonts = request.values.get('fonts')

	# Anonymous App ID
	# String anonymously identifying one app installation on one computer
	anonymousAppID = request.values.get('anonymousAppID')

	# Anonymous Type.World User ID
	# Anonymous string identifying one Type.World user account, which could be used across several app instances
	anonymousTypeWorldUserID = request.values.get('anonymousTypeWorldUserID')

	# User Name and Email
	# In case you require it and the user has accepted to reveal their identity when installing fonts, 
	# this parameter will hold the user’s name as per their Type.World user account.
	# For privacy reasons, the validity of this name can’t be verified, so you need to take it as is.
	# If the user changes the name in their user account, you can’t get to know about that until a new
	# font installattion request comes in with the new name.
	userName = request.values.get('userName')
	userEmail = request.values.get('userEmail')

	# We’ve processed all possible incoming data, so let’s create the root object
	# See: https://github.com/typeworld/typeworld/tree/master/Lib/typeworld/api#user-content-class-rootresponse
	root = typeworld.api.RootResponse()

	# Process the commands in the order they were given.
	# It is mandatory that they are executed in the given order to retain certain logic.
	# For example, when installing a "protected" font, the `installFonts` command is defined
	# and you are expected to build that command and include the requested fonts in it.
	# Afterwards, you want to update the amount of seats used for this font’s license,
	# and not the other way around, as requested in the `installableFonts` command
	# Therefore, the `commands` parameter will have the commands defined in the order `installFonts,installableFonts`

	# Generally, several commands are combined into one root object for speed of execution. 
	# Instead of starting several HTTP requests, one for `installFonts` and another for `installableFonts`,
	# they are combined into one request and returned combined in one root object.
	# Not only does this speed up the work on your server, but in case of protected fonts you would have to
	# ask the central type.world server for user verification twice, too, which introduces a lot of 
	# unnecessary overhead. So we’re streamlining things a lot here by combining them.

	for command in commandsList:

		# Call endpoint() method, hand over root object to fill with data
		if command == 'endpoint':
			endpoint(root)

		# Call installableFonts() method, hand over root object to fill with data
		elif command == 'installableFonts':
			installableFonts(root)

		# Call installFonts() method, hand over root object to fill with data
		elif command == 'installFonts':
			installFonts(root)

		# Call uninstallFonts() method, hand over root object to fill with data
		elif command == 'uninstallFonts':
			uninstallFonts(root)

	# Export root object into nicely formatted JSON data
	jsonData = root.dumpJSON()

	# Return the response with the correct MIME type `application/json` (or otherwise the app will complain)
	return Response(jsonData, mimetype='application/json')


# Run this web server locally under https://127.0.0.1:8080/
if __name__ == '__main__':
	app.run(host='127.0.0.1', port=8080, debug=False)
