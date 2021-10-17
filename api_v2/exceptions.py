class NotAllowedAction(Exception):
    def __init__(self, method, *args):
        self.method = method
        super().__init__(*args)
