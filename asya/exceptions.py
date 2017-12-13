
class AsyaException(Exception):
    """
    Exception of Asya caused during communication with
    the GitHub API

    :ivar data: API response data causing the exception
    :vartype data: dict
    :ivar headers: API response headers causing the exception
    :vartype headers: dict
    """

    def __init__(self, data, headers):
        self.data = data
        self.headers = headers

    @property
    def message(self):
        return '{}: {}'.format(
            self.headers['Status'],
            self.data.get('message', '')
        )
