def log(func):
    def inner(self: "Tester", *args, **kwargs):
        print("invoked")
        return func(self, *args, **kwargs)

    return inner


class Tester:
    @log
    def bark(self, name):
        print("Bark " + name)


t = Tester()

t.bark("Jacob")
