

from parsecp2 import *
import unittest

class XXXX(unittest.TestCase):

    def test_regexp(self):

        p = pR(r"\s*")
        success,s,v = runParser(p,"abcde")
        self.assertTrue( v.word == "" )
        
        success,s,v = runParser(p,"  abcde")
        self.assertTrue( v.word == "  " )
        
    def test_skip(self):
            
        p = pR(r"\w+")
        success,s,v = runParser(p,"abcde")
        self.assertTrue(v.word == "abcde")
        
        success,s,*v = runParser(k(p),"abcde")
        self.assertTrue(v == [])
        
    def test_do(self):
        
        p = d(word("a"),word("b"),word("c"))
        success,s,*v = runParser(p,"abcde")
        self.assertTrue(v == ["a","b","c"])
        
    def test_cl(self):
            
        p = c(digit(),
              word("+") >> (lambda _: (lambda n,m: n+m)) )
        success,s,v = runParser(p,"1 + 2")
        self.assertTrue(v == 3)
        
    def test_ws(self):

        p = pR(r"\s*")
        success,s,v = runParser(p,"")
        self.assertTrue( v.word == "" )
        
        p = pR(r"\s+")
        success,s,*v = runParser(p,"")
        self.assertTrue( v == [] )
        
        p = pS("")
        success,s,v = runParser(p,"")
        self.assertTrue( v.word == "" )
        
    def test_do_operator(self):
            
        p = word("a") + word("b") + word("c")
        success,s,*v = runParser(p,"abcde")
        self.assertTrue(v == ["a","b","c"])

            
    def test_gt_operator(self):

        def add(*w):
            ret = 0
            for i in w:
                ret += i
            return ret
            
        p = digit() + digit() + digit() > add
        success,s,*v = runParser(p,"1 2 3")
        self.assertTrue(v == [6])

    def test_or_operator(self):

        p = word("a") | word("b")
        success,s,*v = runParser(p,"a")
        self.assertTrue(v == ["a"])
        
        success,s,*v = runParser(p,"b")
        self.assertTrue(v == ["b"])

if __name__ == "__main__":
    unittest.main()
    
