# This package will contain the spiders of your Scrapy project
#
# Please refer to the documentation for information on how to create and manage
# your spiders.


class IdentifyingCodeError(Exception):
    """出现验证码所引发的异常"""

    def __init__(self, text):
        self.text = text

    def __str__(self):
        return self.text
