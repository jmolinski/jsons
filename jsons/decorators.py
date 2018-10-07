"""
This module contains decorators that facilitate the `jsons` functions in an
alternative fashion.
"""
import warnings
from inspect import signature, Parameter, isawaitable, iscoroutinefunction
from jsons import JsonSerializable, dump, load


def loaded(parameters=True, returnvalue=True, fork_inst=JsonSerializable,
           **kwargs):
    """
    Return a decorator that can call `jsons.load` upon all parameters and the
    return value of the decorated function.


    **Example**:

    >>> from datetime import datetime
    >>> @loaded()
    ... def func(arg: datetime) -> datetime:
    ...     # arg is now of type datetime.
    ...     return '2018-10-04T21:57:00Z'  # This will become a datetime.
    >>> res = func('2018-10-04T21:57:00Z')
    >>> type(res).__name__
    'datetime'

    :param parameters: determines whether parameters should be taken into
    account.
    :param returnvalue: determines whether the return value should be taken
    into account.
    :param fork_inst: if given, it uses this fork of ``JsonSerializable``.
    :param kwargs: any keyword arguments that should be passed on to
    `jsons.load`
    :return: a decorator that can be placed on a function.
    """
    return _get_decorator(parameters, returnvalue, fork_inst, load, kwargs)


def dumped(parameters=True, returnvalue=True, fork_inst=JsonSerializable,
           **kwargs):
    """
    Return a decorator that can call `jsons.dump` upon all parameters and the
    return value of the decorated function.


    **Example**:

    >>> from datetime import datetime
    >>> @dumped()
    ... def func(arg):
    ...     # arg is now of type str.
    ...     return datetime.now()
    >>> res = func(datetime.now())
    >>> type(res).__name__
    'str'

    :param parameters: determines whether parameters should be taken into
    account.
    :param returnvalue: determines whether the return value should be taken
    into account.
    :param fork_inst: if given, it uses this fork of ``JsonSerializable``.
    :param kwargs: any keyword arguments that should be passed on to
    `jsons.dump`
    :return: a decorator that can be placed on a function.
    """
    return _get_decorator(parameters, returnvalue, fork_inst, dump, kwargs)


def _get_params_sig(args, func):
    sig = signature(func)
    params = sig.parameters
    param_names = [param_name for param_name in params]
    result = [(args[i], params[param_names[i]]) for i in range(len(args))]
    return result


def _map_args(args, decorated, fork_inst, mapper, mapper_kwargs):
    params_sig = _get_params_sig(args, decorated)
    new_args = []
    for arg, sig in params_sig:
        if sig.name in ('self', 'cls') and hasattr(arg, decorated.__name__):
            # `decorated` is a method and arg is either `self` or `cls`.
            new_arg = arg
        else:
            cls = sig.annotation if sig.annotation != Parameter.empty else None
            new_arg = mapper(arg, cls=cls, fork_inst=fork_inst,
                             **mapper_kwargs)

        new_args.append(new_arg)
    return new_args


def _map_returnvalue(returnvalue, decorated, fork_inst, mapper, mapper_kwargs):
    return_annotation = signature(decorated).return_annotation
    cls = return_annotation if return_annotation != Parameter.empty else None
    result = mapper(returnvalue, cls=cls, fork_inst=fork_inst, **mapper_kwargs)
    return result


def _run_decorated(decorated, mapper, fork_inst, args, kwargs, mapper_kwargs):
    new_args = args
    if mapper:
        new_args = _map_args(args, decorated, fork_inst, mapper, mapper_kwargs)
    result = decorated(*new_args, **kwargs)
    return result


def _get_decorator(parameters, returnvalue, fork_inst, mapper, mapper_kwargs):
    def _decorator(decorated):
        def _wrapper(*args, **kwargs):
            result = _run_decorated(decorated, mapper if parameters else None,
                                    fork_inst, args, kwargs, mapper_kwargs)
            if returnvalue:
                result = _map_returnvalue(result, decorated, fork_inst, mapper,
                                          mapper_kwargs)
            return result

        async def _async_wrapper(*args, **kwargs):
            result = _run_decorated(decorated, mapper if parameters else None,
                                    fork_inst, args, kwargs, mapper_kwargs)
            if isawaitable(result):
                result = await result
            if returnvalue:
                result = _map_returnvalue(result, decorated, fork_inst, mapper,
                                          mapper_kwargs)
            return result
        if isinstance(decorated, staticmethod):
            warnings.warn('You cannot decorate a static- or classmethod. '
                          'You can still obtain the desired behaviour by '
                          'decorating your method first and then place '
                          '@staticmethod/@classmethod on top (switching the '
                          'order).')
            raise Exception('Cannot decorate a static- or classmethod.')
        if isinstance(decorated, type):
            raise Exception('Cannot decorate a class.')
        return _async_wrapper if iscoroutinefunction(decorated) else _wrapper
    return _decorator