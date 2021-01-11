# Import typeworld module
import typeworld.api
import typeworld.client

# Import JSON module
import json

# Import Flask web server
from flask import Flask, Response, request, abort

global app
app = Flask(__name__)

# Main API Endpoint URL
# For security reasons (so that URLs don’t show up in server logs anywhere),
# we’re only allowing POST requests, where data is transmitted hidden in the requests’ HTTP headers
@app.route("/api", methods=["POST"])
def api():

    # SECURITY WARNING:
    # Please note that it’s your responsibility to quarantine all incoming data against SQL injections attacks etc.

    # Only the `commands` parameter is required at this point. All other parameters are optional until we
    # deal with the respective commands, where they will be checked for being present.

    # API Commands (required)
    # Comma-separated list of commands such as "installFonts,installableFonts".
    # It is critical that they are executed in the order defined in this incoming parameter.
    # See: https://github.com/typeworld/typeworld/tree/master/Lib/typeworld/api#user-content-class-rootresponse
    commands = request.values.get("commands")

    # `commands` is a required parameter. If it’s missing, return the request immediately with 404 Not Found
    # All valid requests must carry `commands`. If they don’t, they are probably not coming from the Type.World App.
    # You can use this as a cheap first step to to sort valid from invalid traffic
    if not commands:
        return handleAbort(404)

    # Otherwise, parse commands into list:
    commandsList = commands.split(",")

    # Subscription ID
    # String identifying a subscription on your server.
    # For example, the user account of your commercial font customer
    # could be identified by an anonymous ID.
    # You have made the `subscriptionID` known to the Type.World app as part of the subscription URL.
    # See: https://type.world/developer#the-subscription-url
    subscriptionID = request.values.get("subscriptionID")

    # Secret Key
    # String as a secret key to a subscription on your server.
    # You have made the `secretKey` known to the Type.World app as part of the subscription URL.
    # See: https://type.world/developer#the-subscription-url
    # And: https://type.world/developer#security-levels
    secretKey = request.values.get("secretKey")

    # Access Token
    # Single-use access token to identify that users are accessing this link from inside your website’s user account.
    # You have made the `accessToken` known to the Type.World app as part of the subscription URL.
    # See: https://type.world/developer#the-subscription-url
    # And: https://type.world/developer#security-levels
    accessToken = request.values.get("accessToken")

    # Fonts
    # Comma-separated list of `fontID`s to install or uninstall
    fonts = request.values.get("fonts")

    # Anonymous App ID
    # String anonymously identifying one app installation on one computer
    anonymousAppID = request.values.get("anonymousAppID")

    # Anonymous Type.World User ID
    # Anonymous string identifying one Type.World user account, which could be used across several app instances
    anonymousTypeWorldUserID = request.values.get("anonymousTypeWorldUserID")

    # User Name and Email
    # In case you require it and the user has accepted to reveal their identity when installing fonts,
    # this parameter will hold the user’s name as per their Type.World user account.
    # For privacy reasons, the validity of this name can’t be verified, so you need to take it as is.
    # If the user changes the name in their user account, you can’t get to know about that until a new
    # font installattion request comes in with the new name.
    userName = request.values.get("userName")
    userEmail = request.values.get("userEmail")

    # App Version
    # Holds the version number of the typeworld module used in the app that this request originates from.
    # This is for future use in case we need to react to protocol changes on our side in the future.
    # Unused for now
    appVersion = request.values.get("appVersion")

    # Verified Type.World User
    # For protected fonts for the three commands `installableFonts`, `installFonts`, and `uninstallFonts`
    # we need to verify whether the `anonymousTypeWorldUserID` is valid and whether it holds this subscription.
    # We’re defining the variable `verifiedTypeWorldUserCredentials` here to None (= undefined), and will hand it over to
    # the three methods installableFonts(), installFonts(), and uninstallFonts(), respectively.
    # When necessary, those three methods will then verify the user credentials with the central type.world server
    # and save the result into `verifiedTypeWorldUserCredentials`, so that the remaining methods don’t need
    # to repeat the verification process, to save time and resources.
    verifiedTypeWorldUserCredentials = None

    # We’ve processed all possible incoming data, so let’s create the root object
    # See: https://github.com/typeworld/typeworld/tree/master/Lib/typeworld/api#user-content-class-rootresponse
    root = typeworld.api.RootResponse()

    # SubscriptionURL
    # For various processing purposes, we need to assemble a complete subscriptionURL here
    # The below example assumes a protected subscription with ID and secret key as per subscription URL Format C
    # (see: https://type.world/developer#the-subscription-url)
    subscriptionURL = (
        f"typeworld://json+{subscriptionID}:{secretKey}@awesomefonts.com/api"
    )

    # API Key
    # Each API Endpoint needs to possess a secret API Key to use when accessing certain commands of the central
    # Type.World server API, first and foremost the user verification.
    # You can obtain such an API Key by registering your API Endpoint in the user account section on https://type.world
    APIKey = "__APIKey__"

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
        if command == "endpoint":

            # Call endpoint()
            success, message = endpoint(root)

            # Process: Return value is of type integer, which means we handle a request abort with HTTP code
            if not success and type(message) == int:
                return handleAbort(message)

        # Call installableFonts() method, hand over root object to fill with data
        elif command == "installableFonts":

            # Call installableFonts()
            success, message = installableFonts(
                root,
                subscriptionURL,
                APIKey,
                subscriptionID,
                secretKey,
                accessToken,
                anonymousAppID,
                anonymousTypeWorldUserID,
                verifiedTypeWorldUserCredentials,
            )

            # Process: Return value is of type integer, which means we handle a request abort with HTTP code
            if not success and type(message) == int:
                return handleAbort(message)

        # Call installFonts() method, hand over root object to fill with data
        elif command == "installFonts":

            # Call installFonts()
            success, message = installFonts(
                root,
                fonts,
                subscriptionURL,
                APIKey,
                subscriptionID,
                secretKey,
                accessToken,
                anonymousAppID,
                anonymousTypeWorldUserID,
                verifiedTypeWorldUserCredentials,
                userName,
                userEmail,
            )

            # Process: Return value is of type integer, which means we handle a request abort with HTTP code
            if not success and type(message) == int:
                return handleAbort(message)

        # Call uninstallFonts() method, hand over root object to fill with data
        elif command == "uninstallFonts":

            # Call uninstallFonts()
            success, message = uninstallFonts(
                root,
                fonts,
                subscriptionURL,
                APIKey,
                subscriptionID,
                secretKey,
                accessToken,
                anonymousAppID,
                anonymousTypeWorldUserID,
                verifiedTypeWorldUserCredentials,
            )

            # Process: Return value is of type integer, which means we handle a request abort with HTTP code
            if not success and type(message) == int:
                return handleAbort(message)

    # Export root object into nicely formatted JSON data.
    # This is the moment of truth if you have indeed used the Python object tree as provided by `typeworld.api`.
    # While individual attributes have already been checked earlier, when they were set, here the entire
    # object tree will undergo a validation process to see that all data has been put together in a logical way
    # and that nothing is missing.
    # If you are not using `typeworld.api` or are implementing your server in another programming language,
    # please validate your server using the online validator at https://type.world/developer/validate
    # In the future, the validator will also be made available offline in `typeworld.tools`
    jsonData = root.dumpJSON()

    # Return the response with the correct MIME type `application/json` (or otherwise the app will complain)
    return Response(jsonData, mimetype="application/json")


def endpoint(root):
    """
    Process `endpoint` command
    """

    # Create `endpoint` object, attach to `root`
    endpoint = typeworld.api.EndpointResponse()
    root.endpoint = endpoint

    # Apply data
    endpoint.name.en = "Awesome Fonts"
    endpoint.name.de = "Geile Schriften"
    endpoint.canonicalURL = "https://awesomefonts.com/api"
    endpoint.websiteURL = "https://awesomefonts.com"
    endpoint.adminEmail = "admin@awesomefonts.com"
    endpoint.supportedCommands = [
        "endpoint",
        "installableFonts",
        "installFonts",
        "uninstallFonts",
    ]
    # etc ...

    # Return successfully, no message
    return True, None


def installableFonts(
    root,
    subscriptionURL,
    APIKey,
    subscriptionID,
    secretKey,
    accessToken,
    anonymousAppID,
    anonymousTypeWorldUserID,
    verifiedTypeWorldUserCredentials,
):
    """
    Process `installableFonts` command
    """

    # Create `installableFonts` object, attach to `root`
    installableFonts = typeworld.api.InstallableFontsResponse()
    root.installableFonts = installableFonts

    # `subscriptionID` is set, so we need to find a particular subscription/user account and serve it
    if subscriptionID:

        # Find user
        __user__ = __userBySubscriptionID__(subscriptionID)

        # User doesn't exist, return `validTypeWorldUserAccountRequired` immediately
        if __user__ == None:
            installableFonts.response = "validTypeWorldUserAccountRequired"
            return True, None

        # Secret Key doesn't match with user, return `insufficientPermission` immediately
        if secretKey != __user__.__secretKey__:
            installableFonts.response = "insufficientPermission"
            return True, None

        ##################################################################
        # Beginning of SECURITY CHECK

        # Either single-use accessToken needs to match, or we need to verify user with type.world server.
        # Corresponds to "Security Level 2" (see: https://type.world/developer#security-levels)

        # Note: `accessToken` is only ever defined for an `installableFonts` command, as it is only ever used once
        # when accessing a subscription for the first time. In the two other methods that have a security check,
        # installFonts() and uninstallFonts(), we’ll solely rely on `verifiedTypeWorldUserCredentials`, as by that time
        # a subscription has already been accessed at least once, and `accessToken` already processed.

        # Set intial state to False
        securityCheckPassed = False

        # Request has a valid single-use access token for this user, so we allow the request
        if accessToken and accessToken == __user__.__accessToken__:
            securityCheckPassed = True

            # Since the access token is single-use, we need to invalidate it here and assign a new one immediately.
            # Also, in case anything goes wrong in the whole setup process of a subscription in the Type.World app,
            # you need to make sure that in your website’s download section, where the user clicked on the button to get here,
            # that button needs to be reloaded with the new accessToken as part of the subscription URL.
            __user__.__assignNewAccessToken__()

        # Security check is still not passed
        if securityCheckPassed == False:

            # See if the user has already been verified
            if verifiedTypeWorldUserCredentials != None:

                # User has been successfully verified before
                if verifiedTypeWorldUserCredentials == True:
                    securityCheckPassed = True

            # Has not been verified yet, so we need to verify them now
            else:
                # Verify user with central type.world server now, save into global variable `verifiedTypeWorldUserCredentials`
                verifiedTypeWorldUserCredentials = verifyUserCredentials(
                    APIKey, anonymousAppID, anonymousTypeWorldUserID, subscriptionURL
                )

                # User was successfully validated:
                if verifiedTypeWorldUserCredentials == True:
                    securityCheckPassed = True

        # Still didn’t pass security check, return `insufficientPermission` immediately
        if securityCheckPassed == False:
            installableFonts.response = "insufficientPermission"
            return True, None

        # End of SECURITY CHECK
        ##################################################################

        # Now we’re passed the security check and may continue ...

        # Pull data out of your own data source
        # Note: __subscriptionDataSource__() doesn’t exist in this sample code
        __ownDataSource__ = __user__.__subscriptionDataSource__()

        # Create object tree for `installableFonts` out of font data in `__ownDataSource__`
        success, message = createInstallableFontsObjectTree(
            installableFonts, __ownDataSource__
        )

        # Process: Return value is of type integer, which means we handle a request abort with HTTP code
        if not success and type(message) == int:
            return False, message

    # `subscriptionID` is empty. We have two choices here:
    # Either we serve only protected fonts, in which case we require a `subscriptionID`, so we return an abort here
    # or we have a general selection of free fonts to serve for whenever no `subscriptionID` is defined
    else:

        # Choose either scenario:

        # Scenario 1: Only protected fonts, so quit here with HTTP Code 401 Unauthorized
        return False, 401

        # -- or --

        # Scenario 2: Serve free fonts

        # Pull data out of your own data source
        # Note: __freeFontDataSource__() doesn’t exist in this sample code
        __ownDataSource__ = __freeFontDataSource__()

        # Create object tree for `installableFonts` out of free font data in `__ownDataSource__`
        success, message = createInstallableFontsObjectTree(
            installableFonts, __ownDataSource__
        )

        # Process: Return value is of type integer, which means we handle a request abort with HTTP code
        if not success and type(message) == int:
            return False, message

    # Successful code execution until here, so we set the response value to 'success'
    installableFonts.response = "success"

    # Return successfully, no message
    return True, None


def installFonts(
    root,
    fonts,
    subscriptionURL,
    APIKey,
    subscriptionID,
    secretKey,
    accessToken,
    anonymousAppID,
    anonymousTypeWorldUserID,
    verifiedTypeWorldUserCredentials,
    userName,
    userEmail,
):
    """
    Process `installFonts` command
    """

    # Create `installFonts` object, attach to `root`
    installFonts = typeworld.api.InstallFontsResponse()
    root.installFonts = installableFonts

    # Find user
    __user__ = __userBySubscriptionID__(subscriptionID)

    # User doesn't exist, return `validTypeWorldUserAccountRequired` immediately
    if __user__ == None:
        installableFonts.response = "validTypeWorldUserAccountRequired"
        return True, None

    # Secret Key doesn't match with user, return `insufficientPermission` immediately
    if secretKey != __user__.__secretKey__:
        installableFonts.response = "insufficientPermission"
        return True, None

    # TODO for later: Add `loginRequired` response here
    # TODO for later: Add `revealedUserIdentityRequired` response here

    ##################################################################
    # Beginning of SECURITY CHECK

    # At this point, in installFonts(), the subscription’s single-use access token has already been verified earlier, so we need not process it here anymore.

    # Set intial state to False
    securityCheckPassed = False

    # See if the user has already been verified
    if verifiedTypeWorldUserCredentials != None:

        # User has been successfully verified before
        if verifiedTypeWorldUserCredentials == True:
            securityCheckPassed = True

    # Has not been verified yet, so we need to verify them now
    else:
        # Verify user with central type.world server now, save into global variable `verifiedTypeWorldUserCredentials`
        verifiedTypeWorldUserCredentials = verifyUserCredentials(
            APIKey, anonymousAppID, anonymousTypeWorldUserID, subscriptionURL
        )

        # User was successfully validated:
        if verifiedTypeWorldUserCredentials == True:
            securityCheckPassed = True

    # Still didn’t pass security check, return `insufficientPermission` immediately
    if securityCheckPassed == False:
        installableFonts.response = "insufficientPermission"
        return True, None

    # End of SECURITY CHECK
    ##################################################################

    # Now we’re passed the security check and may continue ...

    # Pull data out of your own data source
    # Note: __subscriptionDataSource__() doesn’t exist in this sample code
    __ownDataSource__ = __user__.__subscriptionDataSource__()

    # Create object tree for `installFonts` out of font data in `__ownDataSource__`
    success, message = createInstallFontsObjectTree(
        installFonts,
        fonts,
        subscriptionID,
        anonymousAppID,
        userName,
        userEmail,
        __ownDataSource__,
    )

    # Process: Return value is of type integer, which means we handle a request abort with HTTP code
    if not success and type(message) == int:
        return False, message

    # Successful code execution until here, so we set the response value to 'success'
    installFonts.response = "success"

    # Return successfully, no message
    return True, None


def uninstallFonts(
    root,
    fonts,
    subscriptionURL,
    APIKey,
    subscriptionID,
    secretKey,
    accessToken,
    anonymousAppID,
    anonymousTypeWorldUserID,
    verifiedTypeWorldUserCredentials,
):
    """
    Process `uninstallFonts` command
    """

    # Create `uninstallFonts` object, attach to `root`
    uninstallFonts = typeworld.api.UninstallFontsResponse()
    root.uninstallFonts = uninstallFonts

    # Find user
    __user__ = __userBySubscriptionID__(subscriptionID)

    # User doesn't exist, return `validTypeWorldUserAccountRequired` immediately
    if __user__ == None:
        installableFonts.response = "validTypeWorldUserAccountRequired"
        return True, None

    # Secret Key doesn't match with user, return `insufficientPermission` immediately
    if secretKey != __user__.__secretKey__:
        installableFonts.response = "insufficientPermission"
        return True, None

    ##################################################################
    # Beginning of SECURITY CHECK

    # At this point, in installFonts(), the subscription’s single-use access token has already been verified earlier, so we need not process it here anymore.

    # Set intial state to False
    securityCheckPassed = False

    # See if the user has already been verified
    if verifiedTypeWorldUserCredentials != None:

        # User has been successfully verified before
        if verifiedTypeWorldUserCredentials == True:
            securityCheckPassed = True

    # Has not been verified yet, so we need to verify them now
    else:
        # Verify user with central type.world server now, save into global variable `verifiedTypeWorldUserCredentials`
        verifiedTypeWorldUserCredentials = verifyUserCredentials(
            APIKey, anonymousAppID, anonymousTypeWorldUserID, subscriptionURL
        )

        # User was successfully validated:
        if verifiedTypeWorldUserCredentials == True:
            securityCheckPassed = True

    # Still didn’t pass security check, return `insufficientPermission` immediately
    if securityCheckPassed == False:
        installableFonts.response = "insufficientPermission"
        return True, None

    # End of SECURITY CHECK
    ##################################################################

    # Now we’re passed the security check and may continue ...

    # Pull data out of your own data source
    # Note: __subscriptionDataSource__() doesn’t exist in this sample code
    __ownDataSource__ = __user__.__subscriptionDataSource__()

    # Create object tree for `uninstallFonts` out of font data in `__ownDataSource__`
    success, message = createUninstallFontsObjectTree(
        installFonts, fonts, subscriptionID, anonymousAppID, __ownDataSource__
    )

    # Process: Return value is of type integer, which means we handle a request abort with HTTP code
    if not success and type(message) == int:
        return False, message

    # Successful code execution until here, so we set the response value to 'success'
    uninstallFonts.response = "success"

    # Return successfully, no message
    return True, None


def createInstallableFontsObjectTree(installableFonts, __ownDataSource__):
    """
    Apply incoming data of `__ownDataSource__` to `installableFonts`.

    This sample code here is very abstract and incomplete.
    Each font publisher has their own database structure and therefore
    a complete example cannot be created.
    You may not even want to use __ownDataSource__ or this method at all.

    Basically, you need to fill in all the minimal required data (and more) into
    the object structure indicated below following your own logic.
    The object structure is defined in detail here:
    https://github.com/typeworld/typeworld/tree/master/Lib/typeworld/api
    """

    # Designers
    for __designerDataSource__ in __ownDataSource__.__designers__():

        # Create Designer object, attach to `installableFonts.designers`, apply data
        designer = typeworld.api.Designer()
        installableFonts.designers.append(designer)

        # Apply data
        designer.keyword = __designerDataSource__.__keyword__
        designer.name.en = __designerDataSource__.__name__
        # etc ...

    # Foundry
    for __foundryDataSource__ in __ownDataSource__.__foundries__():

        # Create Foundry object, attach to `installableFonts.foundries`, apply data
        foundry = typeworld.api.Foundry()
        installableFonts.foundry.append(foundry)

        # Apply data
        designer.keyword = __foundryDataSource__.__keyword__
        designer.name.en = __foundryDataSource__.__name__
        # etc ...

        # License Definitions
        for __licenseDataSource__ in __foundryDataSource__.licenses():

            # Create LicenseDefinition object, attach to `foundry`
            licenseDefition = typeworld.api.LicenseDefinition()
            foundry.licenses.append(licenseDefition)

            # Apply data
            licenseDefition.keyword = __licenseDataSource__.__keyword__
            # etc ...

        # Families
        for __familyDataSource__ in __foundryDataSource__.licenses():

            # Create Family object, attach to `foundry`
            family = typeworld.api.Family()
            foundry.families.append(family)

            # Apply data
            family.uniqueID = __familyDataSource__.__uniqueID__
            # etc ...

            # Family-level Font Versions
            # Here, we’re defining family-wide font versions.
            # You could also set the on font-level instead, or a combination of both
            for __versionDataSource__ in __familyDataSource__.__versions__():

                # Create Version object, attach to `family.versions`
                version = typeworld.api.Version()
                family.versions.append(version)

                # Apply data
                version.number = __versionDataSource__.__versionNumber__
                # etc ...

            # Fonts
            for __fontDataSource__ in __familyDataSource__.__fonts__():

                # Create Font object, attach to `family.fonts`
                font = typeworld.api.Font()
                family.fonts.append(font)

                # Apply data
                font.uniqueID = __fontDataSource__.__uniqueID__
                # etc ...

    # Return successfully, no message
    return True, None


def createInstallFontsObjectTree(
    installFonts,
    fonts,
    subscriptionID,
    anonymousAppID,
    userName,
    userEmail,
    __ownDataSource__,
):
    """
    Apply incoming data of `__ownDataSource__` to `installFonts`
    """

    # Parse fonts into list
    # They come as comma-separated pairs of fontID/fontVersion, so
    # "font1ID/font1Version,font2ID/font2Version" becomes [['font1ID', 'font1Version'], ['font2ID', 'font2Version']]
    fontsList = [x.split("/") for x in fonts.split(",")]

    # Loop over incoming fonts list
    for fontID, fontVersion in fontsList:

        # Load own data source
        __fontDataSource__ = __ownDataSource__.__fontDataSource__(fontID)

        # Create InstallFontAsset object, attach to `installFonts.assets`
        asset = typeworld.api.InstallFontAsset()
        installFonts.assets.append(asset)

        # Couldn't find data source by ID, return `unknownFont`
        if __fontDataSource__ == None:
            asset.response = "unknownFont"

        # See whether user’s seat allowance has been reached for this font
        seats = __ownDataSource__.__recordedFontInstallations__(
            fontID, subscriptionID, anonymousAppID
        )

        # Installed seats have reached seat allowance, return `seatAllowanceReached`
        if seats >= __fontDataSource__.__licenseDataSource__.__allowedSeats__:
            asset.response = "seatAllowanceReached"

        # All go, let’s serve the font

        # Apply data
        asset.response = "success"
        asset.uniqueID = __fontDataSource__.__uniqueID__
        asset.encoding = "base64"
        asset.mimeType = "font/otf"
        asset.data = __fontDataSource__.__binaryFontData__

        # Font is not a free font
        if __fontDataSource__.__protected__:

            # Finally, let’s record this installation in the database, to count seats for each font per license
            # This call is related to `__fontDataSource__.__recordedFontInstallations__(fontID, subscriptionID, anonymousAppID)` from above where
            # number of previously installed seats is checked, which is a result of this following recording.
            # The parameters `fontVersion`, `userName`, and `userEmail` are not strictly necessary for this recording, but you may
            # want to save them into your database for analysis.

            # Font is a trial font, so we may have to update previously existing font installation records
            if __fontDataSource__.__isTrialFont__:

                # Font has not been previously installed, so no record exists:
                if seats == None:
                    __ownDataSource__.__recordFontInstallation__(
                        fontID,
                        fontVersion,
                        subscriptionID,
                        anonymousAppID,
                        userName,
                        userEmail,
                    )

                # Font has been previously installed (so a record exists), but is marked as 'uninstalled', so we update that
                else:
                    __ownDataSource__.__updateFontInstallation__(
                        fontID,
                        subscriptionID,
                        anonymousAppID,
                        trialInstalledStatus=True,
                    )

            # Font is not a trial font, so just record installation normally
            else:
                __ownDataSource__.__recordFontInstallation__(
                    fontID,
                    fontVersion,
                    subscriptionID,
                    anonymousAppID,
                    userName,
                    userEmail,
                )

    # Return successfully, no message
    return True, None


def createUninstallFontsObjectTree(
    uninstallFonts,
    fonts,
    subscriptionID,
    anonymousAppID,
    userName,
    userEmail,
    __ownDataSource__,
):
    """
    Apply incoming data of `__ownDataSource__` to `uninstallFonts`
    """

    # Parse fonts into list
    # They come as comma-separated pairs of fontID/fontVersion, so
    # "font1ID,font2ID" becomes ['font1ID', 'font2ID']
    fontsList = fonts.split(",")

    # Loop over incoming fonts list
    for fontID in fontsList:

        # Load own data source
        __fontDataSource__ = __ownDataSource__.__fontDataSource__(fontID)

        # Create UninstallFontAsset object, attach to `uninstallFonts.assets`
        asset = typeworld.api.UninstallFontAsset()
        uninstallFonts.assets.append(asset)

        # Couldn't find data source by ID, set response, return immediately
        if __fontDataSource__ == None:
            asset.response = "unknownFont"

        # See how many seats the user has installed
        seats = __ownDataSource__.__recordedFontInstallations__(
            fontID, subscriptionID, anonymousAppID
        )

        # No seats have been recorded for this `anonymousAppID`, so we return the `unknownInstallation` command
        # Note: This is critical for the remote de-authorization for entire app instances to work properly,
        # and will be checked by the API Endpoint Validator (see: https://type.world/developer/validate)
        # See: https://type.world/developer#remote-de-authorization-of-app-instances-by-the-user
        if seats == None:
            asset.response = "unknownInstallation"

        # All go, let’s delete the font
        asset.response = "success"

        # Font is not a free font
        if __fontDataSource__.__protected__:

            # Finally, let’s delete this installation record from the database

            # Font is a trial font, so instead of deleting this font installation from our records, we’ll just update it, marked as not installed,
            # because if you delete it instead, you effectively reset the the user’s trial period of that font.
            if __fontDataSource__.__isTrialFont__:
                __ownDataSource__.__updateFontInstallation__(
                    fontID, subscriptionID, anonymousAppID, trialInstalledStatus=False
                )

            # Font is not a trial font, so just delete the installation record normally
            else:
                __ownDataSource__.__deleteFontInstallationRecord__(
                    fontID, subscriptionID, anonymousAppID
                )

    # Return successfully, no message
    return True, None


def verifyUserCredentials(
    APIKey, anonymousAppID, anonymousTypeWorldUserID, subscriptionURL=None
):
    """
    Verify a valid Type.World user account with the central server
    """

    # Default parameters
    parameters = {
        "APIKey": APIKey,
        "anonymousTypeWorldUserID": anonymousTypeWorldUserID,
        "anonymousAppID": anonymousAppID,
    }

    # Optional `subscriptionURL` is defined, sadd it
    if subscriptionURL:
        parameters["subscriptionURL"] = subscriptionURL

    # We’re using typeworld’s built-in request() method here which loops through a request up to 10 times
    # in case an instance of the central server disappears during the request.
    # See the WARNING at https://type.world/developer#typeworld-api
    # If you’re implementing this in a language other than Python, make sure to read and follow that warning.
    success, response, responseObject = typeworld.client.request(
        "https://api.type.world/v1/verifyCredentials", parameters
    )

    # Request was successfully returned
    # Note: This means that the HTTP request was successful, not that the user has been verified. This will be confirmed a few lines down.
    if success:

        # Read response data from a JSON string
        responseData = json.loads(response.decode())

        # Verfification process was successful
        if responseData["response"] == "success":

            # Return True immediately
            return True

    # No previous success, so let’s return False
    return False


def handleAbort(code):
    """
    You can use this method to handle all malformed requests.
    Depending on what kind of security shields you have in place, you could keep informing them
    about malformed requests so that eventually a DOS attack shield could kick in, for instance.
    """

    # Handle malformed request here
    # ...

    # Return flask’s abort() method with HTTP status code
    return abort(code)


# Run this web server locally under https://0.0.0.0:8080/
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=False)
