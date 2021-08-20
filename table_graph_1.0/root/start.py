from my_package import app2

app2.__name__ = '__main__' # Make it look like `my_package.__main__` is the main script
app2.run()  # Call your main function if required
