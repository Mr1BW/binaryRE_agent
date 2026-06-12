#!/usr/bin/env python2.7
import os
import sys
import json

def decompile_function():
    print("Decompiling function with Ghidra")

    # Ghidra passes arguments via getScriptArgs()
    args = getScriptArgs()
    if len(args) != 1:
        print("Usage: decompile_function.py <function_name>")
        sys.exit(1)

    function_name = args[0]
    print("Function name: {}".format(function_name))

    # Get the current program
    program = currentProgram
    if not program:
        print("No program loaded")
        sys.exit(1)
        
    # Attempt a symbol search first
    function = None
    symbol_table = program.getSymbolTable()
    symbols = symbol_table.getSymbols(function_name)
    
    if symbols is not None and symbols.hasNext():
        print("Symbol(s) found for '{}'.".format(function_name))
        symbol = symbols.next()  # get first symbol found
        if symbol is not None:
            listing = program.getListing()
            addr = symbol.getAddress()
            function = listing.getFunctionAt(addr)
        else:
            print("Symbol object returned is None for '{}'.".format(function_name))
    else:
        print("No symbol found for '{}'.".format(function_name))
    
    # If symbol search didn't produce a function, fall back to direct function search.
    if function is None:
        print("Attempting function search with getFunction() / getGlobalFunctions()")
        function = getFunction(function_name)
        if not function:
            # Use global search if getFunction didn't work
            functions = getGlobalFunctions(function_name)
            if functions:
                function = functions[0]
            else:
                print("Function '{}' not found by symbol or function search.".format(function_name))
                sys.exit(1)
    
    # Get the decompiler interface
    from ghidra.app.decompiler import DecompInterface
    decompiler = DecompInterface()
    decompiler.openProgram(program)
    
    # Decompile the function
    decompile_results = decompiler.decompileFunction(function, 30, monitor)
    if not decompile_results.decompileCompleted():
        print("Decompilation failed")
        sys.exit(1)
    
    # Get the decompiled code
    decompiled_code = decompile_results.getDecompiledFunction().getC()
    print("/* Decompiled '{}' */".format(function_name))
    print(decompiled_code)

if __name__ == "__main__":
    decompile_function()