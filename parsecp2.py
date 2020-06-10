
"""
     yet another Parsec like parser combinator library for Python
     A implementation by the wrapper class with some operator overloading
"""
__all__ = [ "r","para","f","k","l","m","m1","u","o","d","c","opt","sb","sb1",
            "ws","ws1","pS","pR","token","runParser", "word", "digit" ]

import re
import types

SUCCESS = True
FAILED  = False

class ParserState:

    def __init__(self,str,pos=0,lineno=0,column=0):
        self.str = str
        self.pos = pos
        self.lineno = lineno
        self.column = column

    def __eq__(self,o):
        return self.pos == o.pos

    def __getitem__(self,key):
        return self.str[key]

    def curstr(self):
        return self[self.pos:]

    def forwardPos(self,p):
        str = self.curstr()[0:p]
        nc  = str.count("\n")
        ln  = str.split("\n",-1)
        return ParserState(self.str,
                           self.pos + p,
                           self.lineno + nc,
                           self.column + p if nc == 0 else len(ln[-1]))
    def isEos(self):
        return not (self.pos < len(self.str) )

class Token:

    def __init__(self,word,pos,lineno,column):
        self.word = word
        self.pos = pos
        self.lineno = lineno
        self.column = column

class Parser:

    def __init__(self,parser):
        if isinstance(parser,types.FunctionType) :
            self.parser = parser
        else:
            raise Exception("error")

    def __call__(self,*args,**keys):
        return self.parser(*args,**keys)

    def __add__(self,b):
        return pD(self.parser,b.parser)

    def __gt__(self,func):
        return pA(self.parser,func)

    def __rshift__(self,func):
        return pA(self.parser,func)

    def __or__(self,p):
        return pO(self.parser,p)

    def __and__(self,p):
        return pCl1(self.parser,p)
        
        
# def parser(func):
#     print("decorator parser: {}".format(func))
#     return Parser(func);

def runParser(p,str):
    return p(ParserState(str))


def pChar(pred):
    def parse(s):
        if s.isEos:
            w = pred(s)
            if w != None:
                return (SUCCESS,
                        s.forwardPos(len(w)),
                        Token(w,
                              s.pos,
                              s.lineno,
                              s.column))
            else:
                return (FAILED,s)
        else:
            return (FAILED,s)
    return Parser(parse)


def pNotChar(pred):
    def parse(s):
        if s.isEos:
            w = pred(s)
            if w == None:
                return (SUCCESS,
                        s.forwardPos(1),
                        Token(s.curstr()[0],
                              s.pos,
                              s.lineno,
                              s.column))
            else:
                return (FAILED,s)
        else:
            return (FAILED,s)
    return Parser(parse)

def predString(str):
    def pred(s):
        cur = s.curstr()
        if cur[0:len(str)] == str:
            return str
        else:
            return None
    return pred

def predRegexp(pat):
    prog = re.compile("^" + pat)
    def pred(s):
        m = prog.match(s.curstr())
        if m:
            str = m.group(0)
            return str
        else:
            return None
    return pred

def pS(str):
    return pChar( predString(str) )

def pR(str):
    return pChar( predRegexp(str) )

def pNS(str):
    return pNotChar( predString(str) )
  
def pNR(regexp):
    return pNotChar( predRegexp(regexp) )
  
def pAny():
    return pChar( lambda s: s.curstr[0] )

def pEof():
    return pNotFollowdBy(pAny)

def token(p):
    return pU( pD( pK( pR(r"\s*") ), p ))

def pRef(lazy):
    p = None
    def parse(s):
#        if p == None:
        p = lazy()
        return p(s)
    return Parser(parse)

def pOk(v):
    def parse(s):
        return (SUCCESS,s,v)
    return Parser(parse)

def pFail(str):
    def parse(s):
        if str != None:
            print(str)
        return (FAILED,s)
    return Parser(parse)

# D is for "do"
# the 'monadic' sequence of parsers
def pD(*ps):
    def parse(s):
        ret = []
        for p in ps:
            success,s,*w = p(s)
            if success:
                for v in w:
                    ret.append(v)
            else:
                return (FAILED,s)
        return (SUCCESS,s,*ret)
    return Parser(parse)

# M is for many
# zero or more occurence of p
def pM(p):
    def parse(s):
        ret = []
        while True:
            success,s0,*w = p(s)
            if success:
                ret.append(*w)
                s = s0
            else:
                break
        return (SUCCESS,s,*ret)
    return Parser(parse)

# 1 or more
def pM1(p):
    return pD(p,pM(p))

##### manyTill
# zero or more p ended by endFunc
def pMT (p,endFunc):
    def parse(s):
        ret = []
        while True:
            success,s0,*w = endFunc(s)
            if success:
                return (SUCCESS,s0,*ret)
            else:
                if s0 != s:
                    return (FAILE,s0)
                success,s1,*w = p(s0)
                if success:
                    s = s1
                    ret.append(*w)
                else:
                    return (FAILED,s1)
    return Parser(parse)
                
##### 1 or more p separated by sep
def pSepBy1(p,sep):
    return pD( p,
               pM( pD(pK(sep), p) ) )

def pSepBy(p,sep):
    return pOpt( pSepBy1(p,sep) )


##### 1 or more p separated by sep
# return (p,sep,....,p,sep,p)
def pWithSep1(p,sep):
    return pD( p, pM(pD(sep, p)) )

def pWithSep(p,sep):
    return pOpt( pWithSep1(p,sep) )

##### zero or more p separated by and ended by sep
# return (p,...)
def pEndBy(p,endFunc):
    return pM( pD(p, pK(endFunc) ) )

##### 1 or more p separated by and ended by sep 
# return (p,...)
def pEndBy1(p,endFunc):
    return pM1( pD(p, pK(endFunc) ) )

# 1 or more p separated by sep ,
# and optionaly ended by sep
# return (p,...)
def pSepEndBy1(p,sep):
    def parse(s):
        ok = False
        ret = []
        while True:
            success,s,*w = p(s)
            if success:
                ret.append(*w)
                ok = True
                success,s = sep(s)
                if success:
                    pass
                else:
                    break
            else:
                break
        if ok:
            return (SUCCESS,s,*ret)
        else:
            return (FAILED,s)
    return Parser(parse)

# zero or more
def pSepEndBy(p,sep):
    return pO( pSepEndBy1(p,sep), pK(sep) )

def pChain(p,op,evalFunc):

    def parse(s):
        values = []
        ops    = []
        success,s,*w = p(s)
        if success:
            values.append(*w)
            while True:
                success,s,*w = op(s)
                if success:
                    success,s,*w1 = p(s)
                    if success:
                        ops.append(w[0])
                        values.append(*w1)
                    else:
                        return (FAILED,s)
                else:
                    break
            return (SUCCESS,
                    s,
                    evalFunc(values,ops))
        else:
            return (FAILED,s)
    return Parser(parse)


def pA(p,func):

    def parse(s):
        success,s,*w = p(s)
        if success:
            return (SUCCESS,s,func(*w))
        else:
            return (FAILED,s)
    return Parser(parse)


def pDebug(label,p):
    def parse(s):
      success,s0,*w = p(s)
      if success:
        print("label=" + label + " SUCCESS")
        return (SUCCESS,s0,*w)
      else:
        print("label=" + label + " FAILED")
        return (FAILED,s0)
    return Parser(parse)

# F is for filter
def pF(p,func):
    def parse(s):
        success,s0,*w = p(s)
        if success:
            if func(*w):
                return (SUCCESS,s0,*w)
            else:
                return (FAILED,s)
        else:
            return (FAILED,s0)
    return Parser(parse)

# L is for label
def pL (str,p):
    def parse(s):
        success,s0,*w = p(s)
        if success:
            return (SUCCESS,s0,[str,[*w]])
        else:
            return (FAILED,s0)
    return Parser(parse)

# K is for skip
def pK (p):
    def parse(s):
        success,s0,*_ = p(s)
        if success:
            return (SUCCESS,s0)
        else:
            return (FAILED,s0)
    return Parser(parse)

def pCr1(p,op):

    def evalStack(values,ops):
        vs = values.copy()
        os = ops.copy()
        while len(os) > 0:
            v2 = vs.pop()
            v1 = vs.pop()
            o = os.pop()
            v = o(v1,v2)
            vs.append(v)
        return vs[0]

    return pChain(p,op,evalStack)
    
def pCl1(p,op):    

    def evalStack(values,ops):
        vs = values.copy()
        os = ops.copy()
        vs.reverse()
        os.reverse()
        while len(os) > 0:
            v1 = vs.pop()
            v2 = vs.pop()
            o = os.pop()
            v = o(v1,v2)
            vs.append(v)
        return vs[0]

    return pChain(p,op,evalStack)

# P is for paren
def pP(po,p,pc):
    return pD( pK(po), p, pK(pc) )

# pOpt
def pOpt(p):
    def parse(s):
      success,s0,*w = p(s)
      if success:
          return (SUCCESS,s0,*w)
      else:
          if s0 == s:
              return (SUCCESS,s,None)
          else:
              print("failed at {0}".format(s0))
              return (FAILED,s0)
    return Parser(parse)

# notFollowedBy
def pNotFolloedBy(p):
    def parse(s):
        success,*_ = p(s)
        if not success:
            return (SUCCESS,s)
        else:
            return (FAILED,s)
    return Parser(parse)
            
# lookAhead
def pLookAhead(p):
    def parse(s):
        success,s0,*_ = p(s)
        if success:
            return (SUCCESS,s)
        else:
            if s0 != s:
                print("failed at {0}".format(s0))
                return (FAILED,s0)
            else:
                return (FAILED,s)
    return Parser(parse)

# O is for Or
# the choice combinator
def pO(*ps):
    def parse(s):
        ret = []
        for p in ps:
            success,s0,*w = p(s)
            if success:
                return (SUCCESS,s0,*w)
            elif s0 != s:
                return (FAILED,s0)
        return (FAILED,s)
    return Parser(parse)


# U is for Undo
# the try combinator
def pU(p):
    def parse(s):
        success,s0,*w = p(s)
        if success:
            return (SUCCESS,s0,*w)
        else:
            return (FAILED,s)
    return Parser(parse)

a    = pA
r    = pRef
para = pP
f    = pF
k    = pK
l    = pL
m    = pM
m1   = pM1
u    = pU
o    = pO
d    = pD
c    = pCl1
opt  = pOpt
sb   = pSepBy
sb1  = pSepBy1
ws   = pWithSep
ws1  = pWithSep1

def word(str):
    return a(token(pS(str)), lambda s: s.word)
    
def digit():
    return a(token(pR(r"\d+")), lambda s: int(s.word))


