class Hello:
	statement = "hello"
	number = 3

	@staticmethod
	def static_print():
		print Hello.statement

	@staticmethod
	def print_number():
		print Hello.number