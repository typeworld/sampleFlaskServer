# Dummy Flask Server for the Type.World JSON Protocol

In `app.py` you’ll find a sample implementation for an API Endpoint that serves JSON data under the Type.World JSON Protocol (see: https://github.com/typeworld/typeworld/tree/master/Lib/typeworld/api).

You can use this as a starting point for your own implementation.

This server in **NOT FUNCTIONAL** and needs to be connected to your own environment, databases etc. It provides some guidance to your own implementation, but can’t do the magic for you. You need to do that.

Also, this sample server uses the `typeworld.api` module for creating the object structure, which can then be easily put out as JSON code with `root.dumpJSON()`.

Sadly, this module exists only for Python. If you want to implement your API Endpoint in another server-side programming language, you need to assemble the JSON data structure manually. You’ll find guidance for each object’s JSON code over at https://github.com/typeworld/typeworld/tree/master/Lib/typeworld/api

Currently, only the main method at `api/` is described. The individual methods `endpoint`, `installableFonts`, `installFonts`, and `uninstallFonts` are still missing from this sample server. Coming up soon.