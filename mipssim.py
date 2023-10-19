from abc import ABC, abstractmethod
from collections import namedtuple, Counter
from dataclasses import dataclass
import re

# register file
registers = [5, 3, 0, 1, 6, 2, 4, 12, 9, 2, 10, 0]

# mapping from labels to indices
labels = {}

# program memory representation
progmem = []

# instruction pointer
iptr = 0

def regnumber(regname):
    return int(regname[1:]) - 1

class Inst(ABC):
    _mnemonic = ''
    
    @classmethod
    @property
    def mnemonic(cls):
        return cls._mnemonic
    
    @abstractmethod
    def sem(self):
        pass
    
@dataclass
class Rformat(Inst):
    rd : int
    rs : int
    rt : int
    
@dataclass
class Iformat(Inst):
    rd : int
    rs : int
    imm : int
    
class Semanticless(Inst):
    def sem(self):
        global iptr
        iptr += 1
    
class Add(Rformat):
    def __init__(self, *args, **kwargs):
        super().__init__(*map(regnumber, args), *map(regnumber, kwargs.values()))
    
    _mnemonic = 'add'
        
    def sem(self):
        global iptr, registers
        registers[self.rd] = registers[self.rs] + registers[self.rt]
        iptr += 1
        
class Addi(Iformat):
    def __init__(self, rd, rs, imm):
        super().__init__(regnumber(rd), regnumber(rs), int(imm))
        
    _mnemonic = 'addi'
        
    def sem(self):
        global iptr, registers
        registers[self.rd] = registers[self.rs] + self.imm
        iptr += 1
        
class Nor(Rformat):
    def __init__(self, *args, **kwargs):
        super().__init__(*map(regnumber, args), *map(regnumber, kwargs.values()))
        
    _mnemonic = 'nor'
        
    def sem(self):
        global iptr, registers
        registers[self.rd] = ~(registers[self.rs] | registers[self.rt])
        iptr += 1
        
class Bne(Iformat):
    def __init__(self, rs, rt, label):
        super().__init__(regnumber(rs), regnumber(rt), labels[label]) # let it throw a key error
        
    _mnemonic = 'bne'
        
    def sem(self):
        global iptr
        if registers[self.rd] != registers[self.rs]:
            iptr = self.imm
            
class Lw(Semanticless):
    _mnemonic = 'lw'
    
class Sw(Semanticless):
    _mnemonic = 'sw'

# the dict of instructions that have semantics (lol)
# and a function to convert the three arguments into the appropriate inst
seminsts = {
    'add': Add,
    'addi': Addi,
    'nor': Nor,
    'bne': Bne,
}

nonseminsts = {
    'lw': Lw,
    'sw': Sw,
}

progtext = """\
loop1:
    addi r11, r10, 4
    sw r2, 16(r7)
    nor r3, r2, r6
loop2:
    lw r4, 0(r2)
    lw r8, 0(r3)
    add r5, r4, r8
    nor r6, r3, r5
    sw r6, 0(r2)
    addi r11, r11, -1
    bne r11, r12, loop2
"""


instcount = Counter()
DBG = True

ARGSEP = re.compile('[, ()]+')
def compile(progtext):
    progindex = 0
    for line in progtext.split('\n'): # we're going simple right now
        line = line.strip()
        if not line:
            continue
        
        if line[-1] == ':': # we are looking at a label
            labels[line[:-1]] = progindex
            continue
        
        inst, arglist = line.split(maxsplit=1)
        if inst not in seminsts:
            progmem.append(nonseminsts[inst]())
            progindex += 1
            continue
            
        args = ARGSEP.split(arglist)
        if len(args) != 3:
            print('Syntax error: instructions are', ', '.join(args))
            quit()
            
        progmem.append(seminsts[inst](*args))
        progindex += 1
        
def run():
    while iptr < len(progmem):
        currinst = progmem[iptr]
        
        if DBG:
            print('Instruction pointer:', iptr)
            print('Current instruction is', currinst._mnemonic)
            print(*[f'{r:#10_x}' for r in registers])
            input()
            
        instcount[currinst._mnemonic] += 1
        currinst.sem()
        
compile(progtext)
run()

print('Value for register 9 is:', registers[regnumber('r9')])
print('Instruction prevalence is', instcount)
