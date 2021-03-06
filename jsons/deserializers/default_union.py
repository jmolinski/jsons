from typing import Union
from jsons._common_impl import get_class_name
from jsons._compatibility_impl import get_union_params
from jsons._main_impl import load
from jsons.exceptions import JsonsError, DeserializationError


def default_union_deserializer(obj: object, cls: Union, **kwargs) -> object:
    """
    Deserialize an object to any matching type of the given union. The first
    successful deserialization is returned.
    :param obj: The object that needs deserializing.
    :param cls: The Union type with a generic (e.g. Union[str, int]).
    :param kwargs: Any keyword arguments that are passed through the
    deserialization process.
    :return: An object of the first type of the Union that could be
    deserialized successfully.
    """
    for sub_type in get_union_params(cls):
        try:
            return load(obj, sub_type, **kwargs)
        except JsonsError:
            pass  # Try the next one.
    else:
        fork_inst = kwargs['fork_inst']
        args_msg = ', '.join([get_class_name(cls_, fork_inst=fork_inst)
                              for cls_ in cls.__args__])
        err_msg = ('Could not match the object of type "{}" to any type of '
                   'the Union: {}'.format(str(cls), args_msg))
        raise DeserializationError(err_msg, obj, cls)
