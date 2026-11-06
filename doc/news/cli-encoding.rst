**Fixed:**

* Fixed ``mdstools flatten``, ``unflatten`` and ``update`` failing with a ``UnicodeEncodeError`` on Windows when the output is not UTF-8 encoded (e.g. when it is piped). The commands no longer print a check mark.
