# $Id$

import ast
import location
import copy
import type

import binpac.util as util

class Linkage:
    """The *linkage* of an ~~IDFunction specifies its link-time
    visibility.""" 
                                                                                                                                                                            
    LOCAL = 1                                                                                                                                                               
    """An ~~ID with linkage LOCAL is only visible inside the 
    ~~Module it is implemented in. This is the default linkage.""" 
                                                                                                                                                                            
    EXPORTED = 2                                                                                                                                                            
    """An ~~ID with linkage EXPORTED is visible across all     
    compilation units.
    """                 
    
class ID(ast.Node):
    """Binds a name to a type.
    
    name: string - The name of the ID.
    
    type: ~~Type - The type of the ID.
    
    linkage: ~~Linkage - The linkage of the ID.
    
    imported: bool - True to indicate that this ID was imported from another
    module. This does not change the semantics of the ID in any way but can be
    used to avoid importing it recursively at some later time.
    
    namespace: string - An optional namespace of the ID, i.e., the name of the
    module in which it is defined. 
    
    location: ~~Location - A location to be associated with the ID. 
    
    Note: The class maps the ~~Visitor subtype to :meth:`~type`.
    """
    
    def __init__(self, name, type, linkage=Linkage.LOCAL, namespace=None, location = None, imported=False):
        assert name
        assert type
        
        super(ID, self).__init__(location)
        self._name = name
        self._namespace = namespace.lower() if namespace else None
        self._type = type
        self._linkage = linkage
        self._imported = imported
        self._location = location

    def name(self):
        """Returns the ID's name.
        
        Returns: string - The ID's name.
        """
        return self._name

    def namespace(self):
        """Returns the ID's namespace.
        
        Returns: string - The ID's namespace, or None if it does not have one. The
        namespace will be lower-case.
        """
        return self._namespace
    
    def setNamespace(self, namespace):
        """Sets the ID's namespace.
        
        namespace: string - The new namespace.
        """
        self._namespace = namespace.lower() if namespace else None
        
    def setLinkage(self, linkage):
        """Sets the ID's linkage.
        
        linkage: string - The new linkage.
        """
        self._linkage = linkage
        
    def setName(self, name): 
        """Sets the ID's name.
        
        name: string - The new name.
        """
        self._name =name
    
    def type(self):
        """Returns the ID's type.
        
        Returns: ~~Type - The ID's type.
        """
        return self._type

    def linkage(self):
        """Returns the ID's linkage.
        
        Returns: ~~Linkage - The ID's linkage.
        """
        return self._linkage

    def imported(self):
        """Returns whether the ID was imported from another module.
        
        Returns: bool - True if the ID was imported.
        """
        return self._imported

    def setImportant(self):
        """Marks the ID as being imported from another module."""
        self._imported = True

    def clone(self):
        """Returns a deep-copy of the ID.
        
        Returns: ~~ID - The deep-copy.
        """
        return copy.deep_copy(self)
        
    def __str__(self):
        return self._name

    ### Overidden from ast.Node.
    
    def resolve(self, resolver):
        if resolver.already(self):
            return
        
        self._type = self._type.resolve(resolver)
    
    ### Methods for derived classes to override.    

    def evaluate(self, cg):
        """Generates HILTI code to load the ID's value.
        
        This method must be overidden for all derived class that represent IDs
        that can be directly accessed.
        
        cg: ~~CodeGen - The code generator to use.
        
        Returns: ~~hilti.operand.Operand - An operand representing
        the evaluated ID. 
        """
        util.internal_error("id.evaluate() not overidden for %s" % self.__class__)

    # Visitor support.
    def visitorSubType(self):
        return self._type
    
class Constant(ID):
    """An ID representing a constant value. See ~~ID for arguments not listed
    in the following.
    
    expr: ~~Expression - The expression to initialize the constant with, or
    None for initialization with the default value.
    """
    def __init__(self, name, type, expr, linkage=None, namespace=None, location=None, imported=False):
        super(Constant, self).__init__(name, type, linkage, namespace, location, imported)
        self._expr = expr
        
    def expr(self):
        """Returns the initialization expression for the local.
        
        Returns: ~~Expression - The init expression, or None if none was set.
        """
        return self._expr

    ### Overidden from ast.Node.

    def validate(self, vld):
        if self._expr and self._expr.type() != self.type():
            vld.error("type of initializer expression does not match")
            
        if self._expr and not self._expr.isInit():
            vld.error("expression cannot be used as initializer")

    def pac(self, printer):
        printer.output("const %s: " % self.name(), nl=False)
        self.type().pac(printer)
        printer.output(" = ")
        printer._const.pac(printer)
        printer.output(";", nl=True)
    
    ### Overidden from ID.
    
    def evaluate(self, cg):
        return self.type().hiltiConstant(cg, self._const)
        
class Local(ID):
    """An ID representing a local function variable. See ~~ID for arguments.
    
    expr: ~~Expression - The expression to initialize the local with, or None
    for initialization with the default value.
    """
    def __init__(self, name, type, expr=None, linkage=None, namespace=None, location=None, imported=False):
        super(Local, self).__init__(name, type, linkage, namespace, location, imported)
        self._expr = expr
        
    def expr(self):
        """Returns the initialization expression for the local.
        
        Returns: ~~Expression - The init expression, or None if none was set.
        """
        return self._expr

    ### Overidden from ast.Node.

    def validate(self, vld):
        if self._expr and self._expr.type() != self.type():
            vld.error("type of initializer expression does not match")
            
        if self._expr and not self._expr.isInit():
            vld.error("expression cannot be used as initializer")

    def pac(self):
        printer.output("local %s: " % self.name())
        self.type().pac(printer)
        printer.output(";", nl=True)
        
    ### Overidden from ID.
    
    #def evaluate(self, cg):
    #    # XXX Not yet implemented because we don't have functions yet.
        
class Parameter(ID):
    """An ID representing a function parameter. See ~~ID for arguments.
    """
    def __init__(self, name, type, linkage=None, namespace=None, location=None, imported=False):
        super(Parameter, self).__init__(name, type, linkage, namespace, location, imported)

    ### Overidden from ast.Node.

    def validate(self, vld):
        pass

    def pac(self):
        printer.output("%s: " % self.name())
        self.type().pac(printer)
        
    ### Overidden from ID.
    
    def evaluate(self, cg):
        return cg.builder().idOp(self.name())
        
class Global(ID):
    """An ID representing a module-global variable. See ~~ID for arguments.
    
    expr: ~~Expression - The expression to initialize the global with, or None
    for initialization with the default value.
    """
    def __init__(self, name, type, expr, linkage=None, namespace=None, location=None, imported=False):
        super(Global, self).__init__(name, type, linkage, namespace, location, imported)
        self._expr = expr
        
    def expr(self):
        """Returns the initialization expressopm of the global.
        
        Returns: ~~Expression - The init expression, or None if none was set.
        """
        return self._expr
        
    ### Overidden from ast.Node.

    def validate(self, vld):
        if self._expr and self._expr.type() != self.type():
            vld.error("type of initializer expression does not match")
            
        if self._expr and not self._expr.isInit():
            vld.error("expression cannot be used as initializer")

    def pac(self, printer):
        printer.output("global %s: " % self.name())
        self.type().pac(printer)
        printer.output(";", nl=True)
    
    ### Overidden from ID.
    
    #def evaluate(self, cg):
    #    # XXX Not yet implemented because we don't have globals yet (just
    # typedelc, which however can't appear 

class Type(ID):
    """An ID representing a type-declaration. See ~~ID for arguments.
    """
    def __init__(self, name, type, linkage=None, namespace=None, location=None, imported=False):
        super(Type, self).__init__(name, type, linkage, namespace, location, imported)
        
    ### Overidden from ast.Node.

    def validate(self, vld):
        self.type().validate(vld)

    def pac(self, printer):
        printer.output("type %s = " % self.name())
        self.type().pac(printer)
        printer.output(";", nl=True)
    
    ### Overidden from ID.
    
    def evaluate(self, cg):
        util.internal_error("evaluate must not be called for id.Type")
    
class Attribute(ID):
    """An ID representing the RHS of an attribute expression.  See ~~ID for
    arguments not listed in the following.
    """
    def __init__(self, name, type, location=None):
        super(Attribute, self).__init__(name, type, location=location)

    ### Overidden from ast.Node.

    def validate(self, vld):
        pass

    def pac(self, printer):
        printer.output("%s" % self.name())
        
    ### Overidden from ID.
    
    def evaluate(self, cg):
        util.internal_error("evaluate must not be called for id.Attribute")
        
class Variable(ID):
    """An ID representing a user-defined unit variable. See ~~ID for arguments
    not listed in the following.
    """
    def __init__(self, name, type, location=None):
        super(Variable, self).__init__(name, type, location=location)
        self._hooks = []

    def hooks(self):
        """Returns the hook statements associated with the variable.
        
        Returns: list of ~~UnitHook - The hooks. 
        """
        return self._hooks
        
    def addHook(self, hook):
        """Adds a hook statement to the variable. The statement will be executed
        when the variable is assigned to.
        
        hook: ~~UnitHook - The hook.
        """
        self._hooks += [hook]
        
    ### Overidden from ast.Node.

    def validate(self, vld):
        pass

    def pac(self, printer):
        printer.output("var %s" % self.name())
        
    ### Overidden from ID.
    
    def evaluate(self, cg):
        util.internal_error("evaluate must not be called for id.Variable")
        

class Function(ID):
    """An ID representing an (overloaded) function. 
    
    name: string - The ID's name.
    
    func: ~~OverloadedFunction: The function referenced by this ID.
    """
    def __init__(self, name, func, location=None):
        super(Function, self).__init__(name, func.type(), location=location)
        self._func = func

    def function(self):
        """
        Returns the (overloaded) function referenced by this ID.
        
        Returns: ~~OverloadedFunction - The function.
        """
        return self._func
        
    ### Overidden from ID.

    def resolve(self, resolver):
        self._func.resolve(resolver)
    
    def validate(self, vld):
        self._func.validate(vld)

    def doSimplify(self):
        self._func = self._func.simplify()
        return self
        
    def pac(self, printer):
        printer.output(self.name())
