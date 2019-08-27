class hehe:
    def __init__(self, a):
        self.a = a


a = [1, 1]
d = hehe(a)
print(d.a)
a.append(1)
print(d.a)


def haha(a):
    a.append(1)
    return a


b = haha(a)
print(b)
print(a)
