import math
import random
class Vector:
	def __init__(self,x = 0, y = 0):
		self.x = x
		self.y = y
	def normalize(self):
		a = self.x
		b = self.y
		mag = math.sqrt(a*a + b*b)
		if not mag == 0:	
			self.x = a/mag
			self.y = b/mag
		else:
			pass
			#print("Vector is zero")
		return self
	def setMag(self,mag):
		self.normalize()
		self.x *= mag
		self.y *= mag
	def getMag(self):
		return math.sqrt(self.x * self.x + self.y * self.y)
	def setDir(self,angle):
		self.setAngle(angle)
	def getDir(self):
		return Vector(self.x, self.y).normalize()
	def getAngle(self):
		return math.atan2(self.y, self.x)
	def setAngle(self, angle):
		mag = self.getMag()
		self.x = mag * math.cos(angle)
		self.y = mag * math.sin(angle)
	def get(self):
		return [self.x,self.y]
	def normal(self):
		return Vector(self.y, -self.x)
	def __add__(self,vec):
		return Vector(self[0] + vec[0], self[1] + vec[1])
	def __iadd__(self,vec):
		self[0] += vec[0]
		self[1] += vec[1]
		return self
	def __sub__(self,vec):
		return Vector(self.x - vec.x, self.y - vec.y)
	def __isub__(self,vec):
		self[0] -= vec[0]
		self[1] -= vec[1]
		return self
	def __mul__(self,mag):
		return Vector(self.x * mag, self.y * mag)
	def __rmul__(self,mag):
		return self * mag
	def __imul__(self,mag):
		self.x *= mag
		self.y *= mag
		return self
	def __truediv__(self,mag):
		if mag == 0:
			return self
		return Vector(self.x/mag, self.y/mag)
	def __div__(self, mag):
		if mag == 0:
			return self
		return Vector(self.x//mag, self.y//mag)
	def __floordiv__(self, mag):
		if mag == 0:
			return self
		return Vector(self.x//mag, self.y//mag)
	def __str__(self):
		return "(" + str(self.x) + ", " + str(self.y) + ")"
	def __repr__(self):
		return str(self)
	def repeTile(self,win_width,win_height):
		if self.x > win_width/2:
			self.x -= win_width
		elif self.x < -win_width/2:
			self.x += win_width
		if self.y > win_height/2:
			self.y -= win_height
		elif self.y < -win_height/2:
			self.y += win_height
	def collideTile(self,vel,win_width,win_height):
		if self.x > win_width/2 or self.x < -win_width/2:
			vel.x = -vel.x
		if self.y > win_height/2 or self.y < -win_height/2:
			vel.y = -vel.y
	def zero(self):
		self.x = 0
		self.y = 0
	def one(self):
		self.x = 1
		self.y = 0
	def dot(self,vec):
		return self.x * vec.x + self.y * vec.y
	def limit(self,magUpper, magLower = 0):
		if self.getMag() > magUpper:
			self.setMag(magUpper)
		if self.getMag() < magLower:
			self.setMag(magLower)
	def vec2tup(self):
		return (self.x, self.y)
	def vec2tupint(self):
		return (int(self.x),int(self.y))
	def __getitem__(self, index):
		if index == 0:
			return self.x
		else:
			return self.y
	def __setitem__(self, index, value):
		if index == 0:
			self.x = value
		else:
			self.y = value
	def __len__(self):
		return 2
	def rotate(self, angle):
		x = self.x * math.cos(angle) - self.y * math.sin(angle)
		y = self.x * math.sin(angle) + self.y * math.cos(angle)
		self.x = x
		self.y = y
		return self
	def integer(self):
		self.x = int(self.x)
		self.y = int(self.y)
		return self
	def __eq__(self, other):
		return self[0] == other[0] and self[1] == other[1]
	def __ne__(self, other):
		return not self.__eq__(other)
	def __neg__(self):
		return self * -1
	def __round__(self):
		return Vector(round(self.x), round(self.y))
	def getNormal(self):
		return Vector(-self.y, self.x)

def normalize(vec):
	vecRes = vectorCopy(vec)
	vecRes.normalize()
	return vecRes
	
def vectorUnitRandom():
	x = random.randint(-10000,10000)
	y = random.randint(-10000,10000)
	return Vector(x,y).normalize()

def vectorFromAngle(angle, mag = 1):
	return Vector(mag * math.cos(angle), mag * math.sin(angle))

def rotateVector(vec, angle):
	x = vec[0] * math.cos(angle) - vec[1] * math.sin(angle)
	y = vec[0] * math.sin(angle) + vec[1] * math.cos(angle)
	return Vector(x, y)

def dotProduct(vec1, vec2):
	return vec1.dot(vec2)

def dist(vec1,vec2):
	return math.sqrt((vec2[0] - vec1[0])*(vec2[0] - vec1[0]) + (vec2[1] - vec1[1])*(vec2[1] - vec1[1]))

def distus(vec1, vec2):
	return (vec2[0] - vec1[0])*(vec2[0] - vec1[0]) + (vec2[1] - vec1[1])*(vec2[1] - vec1[1])

def getAngleByTwoVectors(vec_org,vec_taget):
	return math.atan2(vec_taget[1] - vec_org[1], vec_taget[0] - vec_org[0])

def vectorCopy(vec):
	return Vector(vec[0],vec[1])

def vecFromTuple(tup):
	return Vector(tup[0], tup[1])

def tup2vec(tup):
	return Vector(tup[0], tup[1])
