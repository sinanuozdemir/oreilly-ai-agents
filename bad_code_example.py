def test_function(x,y,z):
    unused_var = 42
    if x==y and y==z:
        print("All equal")
    return x+y+z

def complex_function(n):
    if n == 0:
        return 0
    elif n == 1:
        return 1
    elif n == 2:
        return 2
    elif n == 3:
        return 3
    else:
        return n
