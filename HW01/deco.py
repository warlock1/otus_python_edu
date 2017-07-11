#!/usr/bin/env python
# -*- coding: utf-8 -*-

from functools import update_wrapper


def disable(func):
    '''
    Disable a decorator by re-assigning the decorator's name
    to this function. For example, to turn off memoization:

    >>> memo = disable

    '''
    return func


def decorator(func_ext):
    '''
    Decorate a decorator so that it inherits the docstrings
    and stuff from the function it's decorating.
    '''
    def internal_decorator(func):
        def internal_func(*args, **kwargs):
            return func(*args, **kwargs)
        return update_wrapper(internal_func, func_ext)
    return internal_decorator


def countcalls(func):
    '''Decorator that counts calls made to the function decorated.'''
    @decorator(func)
    def internal_func(*args, **kwargs):
        internal_func.calls += 1
        return func(*args, **kwargs)
    internal_func.calls = 0
    return internal_func


def memo(func):
    '''
    Memoize a function so that it caches all return values for
    faster future lookups.
    '''
    cache = {}
    decorator(func)
    def internal_func(*args):
        try:
            if args in cache:
                return cache[args]
            else:
                cache[args] = func(*args)
                return cache[args]
        except TypeError:
            return func(*args)
    return func


def n_ary(func):
    '''
    Given binary function f(x, y), return an n_ary function such
    that f(x, y, z) = f(x, f(y,z)), etc. Also allow f(x) = x.
    '''
    @decorator(func)
    def internal_func(x, *args):
        if len(args) == 0:
            return x
        else:
            return func(x, internal_func(*args))
    return internal_func


def trace(indent):
    '''Trace calls made to function decorated.

    @trace("____")
    def fib(n):
        ....

    >>> fib(3)
     --> fib(3)
    ____ --> fib(2)
    ________ --> fib(1)
    ________ <-- fib(1) == 1
    ________ --> fib(0)
    ________ <-- fib(0) == 1
    ____ <-- fib(2) == 2
    ____ --> fib(1)
    ____ <-- fib(1) == 1
     <-- fib(3) == 3

    '''
    def internal_decorator(func):
        @decorator(func)
        def internal_func(*args, **kwargs):
            args_str = ', '.join(repr(p) for p in args)
            kwargs_str = ', '.join('%s=%s' % (p[0], repr(p[1])) for p in kwargs.items())
            call_params = args_str
            if kwargs_str:
                if call_params:
                    call_params += ', '
                call_params += kwargs_str
            call_func_str = '%s(%s)' % (func.__name__, call_params)
            print indent * internal_func.call_level, '-->', call_func_str
            internal_func.call_level += 1
            try:
                result = func(*args, **kwargs)
                print indent * internal_func.call_level, '<--', call_func_str, '== %s' % repr(result) if result else ''
            finally:
                internal_func.call_level -= 1
            return result
        internal_func.call_level = 0
        return internal_func
    return internal_decorator


@memo
@countcalls
@n_ary
def foo(a, b):
    return a + b


@countcalls
@memo
@n_ary
def bar(a, b):
    return a * b


@countcalls
@trace("####")
@memo
def fib(n):
    return 1 if n <= 1 else fib(n-1) + fib(n-2)


def main():
    print foo(4, 3)
    print foo(4, 3, 2)
    print foo(4, 3)
    print "foo was called", foo.calls, "times"

    print bar(4, 3)
    print bar(4, 3, 2)
    print bar(4, 3, 2, 1)
    print "bar was called", bar.calls, "times"

    print fib.__doc__
    fib(3)
    print fib.calls, 'calls made'


if __name__ == '__main__':
    main()
