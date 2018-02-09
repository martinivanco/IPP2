# File: cls.py                     #
# Project: IPP 2, C++ Classes      #
# Author: Martin Ivanco (xivanc03) #

import sys
import os.path
import xml.etree.ElementTree as ET
import xml.dom.minidom
import re

# Dorobit using (ak sa budes nudit)


########## CLASSES ##########


# Class representing an attribute
class Atr:
	access = ""
	atype = ""
	name = ""
	scope = ""
	inherited = ""

	def __init__(self, access, atype, name, scope, inherited):
		self.access = access
		self.atype = atype
		self.name = name
		self.scope = scope
		self.inherited = inherited

# Class representing parameter
class Par:
	ptype = ""
	name = ""

	def __init__(self, ptype, name):
		self.ptype = ptype
		self.name = name

# Class representing a method
class Met:
	access = ""
	mtype = ""
	name = ""
	scope = ""
	virtual = 0
	inherited = ""
	params = []

	def __init__(self, access, mtype, name, scope, virtual, inherited, params):
		self.access = access
		self.mtype = mtype
		self.name = name
		self.scope = scope
		self.virtual = virtual
		self.inherited = inherited
		self.params = params

	def sameparams(self, met):
		if (len(self.params) != len(met.params)):
			return False

		for i in range(0, len(self.params) - 1):
			if (self.params[i].ptype != met.params[i].ptype):
				return False

		return True

# Class representing a class
class Cla:
	name = ""
	kind = ""
	inheritance = []
	attributes = []
	methods = []

	def __init__(self, name):
		self.name = name
		self.kind = ""
		self.inheritance = []
		self.attributes = []
		self.methods = []

	def set_kind(self):
		self.kind = "concrete"
		for m in self.methods:
			if (m.virtual == 1):
				self.kind = "abstract"

	def add_inheritance(self, tup):
		for t in self.inheritance:
			if (t[1] == tup[1]):
				perror("ERROR: Duplicate class inherition.")
				sys.exit(4) # CHECK THIS ERROR!!!
		self.inheritance.append(tup)

	def add_attribute(self, attr):
		for a in self.attributes:
			if (a.name == attr.name):
				perror("ERROR: Duplicate attribute.")
				sys.exit(21)
		self.attributes.append(attr)

	def add_method(self, met):
		for m in self.methods:
			if (m.name == met.name):
				if ((m.virtual == 1) and (met.virtual == 0) and (m.mtype == met.mtype) and (m.sameparams(met))):
					m.virtual = 0
					return
				if ((m.mtype != met.mtype) or (not m.sameparams(met))):
					perror("ERROR: Duplicate method.")
					sys.exit(21)
		self.methods.append(met)


########## AUXILIARY FUNCTIONS ##########


# Auxiliary function for printing to stderr
def perror(*args, **oargs):
    print(*args, file=sys.stderr, **oargs)

# Auxiliary funcion for parsing arguments
def parse_arguments(inputfname, outputfname, pxmltab, details, dclass):
	if (len(sys.argv) > 1 and sys.argv[1] == "--help"):
		if (len(sys.argv) != 2):
			perror("ERROR: Parameter \"--help\" can't be combined with other arguments.\n")
			sys.exit(1)

		print("Here will be some help.\n")
		sys.exit(0)

	for i in range(1, len(sys.argv)):
		if (sys.argv[i][:8] == "--input="):
			if (inputfname == ""):
				inputfname = sys.argv[i][8:]
			else:
				perror("ERROR: Multiple input file arguments.\n")
				sys.exit(1)

		elif (sys.argv[i][:9] == "--output="):
			if (outputfname == ""):
				outputfname = sys.argv[i][9:]
			else:
				perror("ERROR: Multiple output file arguments.\n")
				sys.exit(1)

		elif (sys.argv[i][:12] == "--pretty-xml"):
			if (pxmltab == -1):
				if (len(sys.argv[i]) > 13):
					if (str.isdigit(sys.argv[i][13:])):
						pxmltab = int(sys.argv[i][13:])
					else:
						perror("ERROR: pretty-xml argument must be specified with a positive number or alone.")
						sys.exit(1)
			else:
				perror("ERROR: Multiple pretty-xml arguments.\n")
				sys.exit(1)

		elif (sys.argv[i][:9] == "--details"):
			if (details == 0):
				details = 1
				if (len(sys.argv[i]) > 10):
					dclass = sys.argv[i][10:]
			else:
				perror("ERROR: Multiple details arguments.\n")
				sys.exit(1)

		else:
			perror("ERROR: Unknown argument.\n")
			sys.exit(1)

	return inputfname, outputfname, pxmltab, details, dclass


########## FUNCTIONS ##########


# Finds the index of class specified by name in the global list of classes
def find_class_index(cname):
	i = 0
	for c in classes:
		if (c.name == cname):
			return i
		i += 1

	return -1

# Finds the parent class to be inherited and adds it to the child class
def get_inheritance(child, parent):
	reg = re.match(r'public\s|protected\s|private\s', parent)
	if (reg == None):
		acc = "private"
		cname = parent
	else:
		acc = reg.group().strip()
		cname = parent[len(reg.group()):].strip()

	intup = (acc, cname)
	ind = find_class_index(cname)
	if (ind == -1):
		perror("ERROR: Inherited class has not yet been defined.")
		sys.exit(4) # CHECK ERROR CODE !!!!!!!

	for a in classes[ind].attributes:
		if (a.access == "private"):
			continue
		nattr = Atr(a.access, a.atype, a.name, a.scope, cname)
		if ((acc == "private") or (acc == "protected")):
			nattr.access = acc
		child.add_attribute(nattr)

	for m in classes[ind].methods:
		if (m.access == "private"):
			continue
		nmet = Met(m.access, m.mtype, m.name, m.scope, m.virtual, cname, m.params)
		if ((acc == "private") or (acc == "protected")):
			nmet.access = acc
		child.add_method(nmet)

	child.add_inheritance(intup)

# Creates class defined by name and adds inheritance dependencies
def create_class(header):
	pos = header.find(":")
	if (pos != -1):
		cname = header[5:pos].strip()
		if (find_class_index(cname) != -1):
			perror("ERROR: Duplicate class definition.")
			sys.exit(4) # CHECK ERROR CODE !!!!!!!
		ncls = Cla(cname)
		header = header[pos + 1:].strip()
		while (1):
			pos = header.find(",")
			if (pos == -1):
				get_inheritance(ncls, header)
				return ncls
			else:
				get_inheritance(ncls, header[:pos].strip())
				header = header[pos + 1:].strip()
	else:
		cname = header[5:].strip()
		if (find_class_index(cname) != -1):
			perror("ERROR: Duplicate class definition.")
			sys.exit(4) # CHECK ERROR CODE !!!!!!!
		return Cla(cname)

# Creates parameter list for method
def get_method_pars(param_list):
	parameters = []

	if (param_list.find("void") == 0):
		if (len(param_list) != 4):
			perror("ERROR: Void must be the only parameter of method.")
			sys.exit(4) # CHECK THIS ERROR!!!!
		else:
			return parameters

	while(param_list != ""):
		ptype = ""
		reg = re.match(r'bool|char16_t|char32_t|char|wchar_t|signed char|short int|int|long int|long long int|unsigned char|unsigned short int|unsigned int|unsigned long int|unsigned long long int|float|double|long double', param_list)
		if (reg == None):
			for n in classes:
				if (source.find(n.name) == 0):
					ptype = n.name
			if (ptype == ""):
				perror("ERROR: Unknown or invalid type!")
				sys.exit(4) # CHECK THIS ERROR!
		else:
			ptype = reg.group()

		param_list= param_list[len(ptype):].strip()
		reg = re.match(r'\*|&', param_list)
		if (reg != None):
			if (reg.group() == "&"):
				ptype += " &amp;"
			else:
				ptype += " *"
			param_list = param_list[1:].strip()

		pos = param_list.find(",")
		if (pos != -1):
			pname = param_list[:pos].strip()
			parameters.append(Par(ptype, pname))
			param_list = param_list[pos + 1:].strip()
		else:
			pname = param_list
			parameters.append(Par(ptype, pname))
			return parameters

# Parses through single class in source while making an alias object of it
def parse_class(source):
	pos = source.find("{")
	nclass = create_class(source[:pos].rstrip())

	source = source[pos + 1:len(source) - 1].strip()
	access = "private"
	while (source != ""):
		if (source[0] == ";"):
			source = source[1:].strip()
			continue

		virt = 0
		scope = "instance"

		reg = re.match(r'public:|protected:|private:', source)
		if (reg != None):
			access = reg.group()
			access = access[:len(access) - 1]
			source = source[len(access) + 1:].strip()
			if (source == ""):
				break

		if (source.find("virtual") == 0):
			virt = 1
			source = source[7:].strip()

		if (source.find("static") == 0):
			scope = "static"
			source = source[7:].strip()

		amtype = ""
		reg = re.match(r'bool|char16_t|char32_t|char|wchar_t|signed char|short int|int|long int|long long int|unsigned char|unsigned short int|unsigned int|unsigned long int|unsigned long long int|float|double|long double|void', source)
		if (reg == None):
			for n in classes:
				if (source.find(n.name) == 0):
					amtype = n.name
			if (amtype == ""):
				if ((source.find(nclass.name) == 0) or (source.find("~" + nclass.name) == 0)):
					amtype = "void"
					source = "void" + source
				else:
					perror("ERROR: Unknown type!")
					sys.exit(4) # CHECK THIS ERROR!
		else:
			amtype = reg.group()
		
		source = source[len(amtype):].strip()
		reg = re.match(r'\*|&', source)
		if (reg != None):
			if (reg.group() == "&"):
				amtype += " &amp;"
			else:
				amtype += " *"
			source = source[1:].strip()

		if (re.search(r'\(|;', source).group() == '('):
			pos = source.find("(")
			mname = source[:pos]
			source = source[pos + 1:]
			pos = source.find(")")
			params = get_method_pars(source[:pos].strip())

			if (virt == 1):
				if (re.search(r'}|;', source).group() == '}'):
					pos = source.find("}")
				else:
					virt == 2
					pos = source.find(";")
			else:
				pos = source.find("}")

			nclass.add_method(Met(access, amtype, mname, scope, virt, "", params))

			source = source[pos + 1:].strip()
		else:
			pos = source.find(";")
			aname = source[:pos]
			nclass.add_attribute(Atr(access, amtype, aname, scope, ""))
			source = source[pos + 1:].strip()

	nclass.set_kind()
	return nclass

# Parses through whole code class after class appending them to global list
def parse_code(source):
	pos = source.find("{")
	i = 0
	while (pos != -1):
		ok = 1

		while (ok != 0):
			par = re.search(r'{|}', source[pos + 1:]).group()
			pos = source.find(par, pos + 1)
			if (par == "{"):
				ok += 1
			else:
				ok -= 1

		classes.append(parse_class(source[:pos + 1].lstrip()))
		source = source[pos + 2:]
		pos = source.find("{")

# Puts class into the XML tree according to its parent
def put_into(model, pname, cname, ckind):
	for el in model.iter("class"):
		if (el.get("name") == pname):
			cl = ET.SubElement(el, "class")
			cl.set("name", cname)
			cl.set("kind", ckind)

# Creates XML class tree using parsed classes
def make_xml_tree():
	model = ET.Element("model")

	for c in classes:
		if (len(c.inheritance) == 0):
			cl = ET.SubElement(model, "class")
			cl.set("name", c.name)
			cl.set("kind", c.kind)
		else:
			for i in c.inheritance:
				put_into(model, i[1], c.name, c.kind)
	
	return model

# Adds attribute to xml details of class
def add_details_attribute(node, a):
	if (node.find("attributes") == None):
		ET.SubElement(node, "attributes")

	attrib = ET.SubElement(node.find("attributes"), "attribute")
	attrib.set("name", a.name)
	attrib.set("type", a.atype)
	attrib.set("scope", a.scope)
	if (a.inherited != ""):
		fr = ET.SubElement(attrib, "from")
		fr.set("name", a.inherited)

# Adds method to xml details of class
def add_details_method(node, m):
	if (node.find("methods") == None):
		ET.SubElement(node, "methods")

	method = ET.SubElement(node.find("methods"), "method")
	method.set("name", m.name)
	method.set("type", m.mtype)
	method.set("scope", m.scope)
	if (m.virtual > 0):
		virt = ET.SubElement(method, "virtual")
		if (m.virtual == 1):
			virt.set("pure", "no")
		else:
			virt.set("pure", "yes")

	if (m.inherited != ""):
		fr = ET.SubElement(method, "from")
		fr.set("name", m.inherited)

	args = ET.SubElement(method, "arguments")
	for p in m.params:
		par = ET.SubElement(args, "argument")
		par.set("name", p.name)
		par.set("type", p.ptype)
		
# Creates XML details about given class
def class_details_xml(name):
	ind = find_class_index(name)
	if (ind == -1):
		perror("ERROR: No such class.")
		sys.exit(1)

	clsnode = ET.Element("class")
	clsnode.set("name", classes[ind].name)
	clsnode.set("kind", classes[ind].kind)

	if (classes[ind].inheritance != []):
		inherit = ET.SubElement(clsnode, "inheritance")
		for i in classes[ind].inheritance:
			fr = ET.SubElement(inherit, "from")
			fr.set("name", i[1])
			fr.set("privacy", i[0])

	priv = None
	prot = None
	publ = None

	for a in classes[ind].attributes:
		if (a.access == "private"):
			if (priv == None):
				priv = ET.SubElement(clsnode, "private")
			add_details_attribute(priv, a)

		elif (a.access == "protected"):
			if (prot == None):
				prot = ET.SubElement(clsnode, "protected")
			add_details_attribute(prot, a)

		elif (a.access == "public"):
			if (publ == None):
				publ = ET.SubElement(clsnode, "public")
			add_details_attribute(publ, a)

	for m in classes[ind].methods:
		if (m.access == "private"):
			if (priv == None):
				priv = ET.SubElement(clsnode, "private")
			add_details_method(priv, m)

		elif (m.access == "protected"):
			if (prot == None):
				prot = ET.SubElement(clsnode, "protected")
			add_details_method(prot, m)

		elif (m.access == "public"):
			if (publ == None):
				publ = ET.SubElement(clsnode, "public")
			add_details_method(publ, m)

	return clsnode

# Makes the XML pretty and returns it in string form
def make_it_pretty(root_node, tab):
	outxml = xml.dom.minidom.parseString(ET.tostring(root_node, encoding="unicode", method="xml"))
	space = " " * tab
	return outxml.toprettyxml(space, encoding="UTF-8")


########## MAIN CODE ##########


inputfname = "" #argument variables
outputfname = ""
pxmltab = -1
details = 0
dclass = ""

inputfname, outputfname, pxmltab, details, dclass = parse_arguments(inputfname, outputfname, pxmltab, details, dclass)

if (inputfname != ""): #filename has been set
	if (os.path.isfile(inputfname) != True):
		perror("ERROR: Given input file doesn't exist.")
		sys.exit(2)
	infile = open(inputfname, "r")
	srcstr = infile.read()
	infile.close()
else: #reading from stdin
	srcstr = sys.stdin.read()

classes = [] #list of classes

parse_code(srcstr)

if (details == 0): #class tree
	root_node = make_xml_tree()
else: #class details
	if (dclass == ""):
		root_node = ET.Element("model")
		for c in classes:
			root_node.append(class_details_xml(c.name))
	else:
		root_node = class_details_xml(dclass)

if (pxmltab == -1):
	pxmltab = 4

outstr = make_it_pretty(root_node, pxmltab)

if (outputfname != ""): #fiename has been set
	outfile = open(outputfname, "w")
	outfile.write(outstr.decode("utf-8"))
	outfile.close()
else: #printing to stdout
	print (outstr.decode("utf-8"))
