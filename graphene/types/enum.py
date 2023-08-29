from collections import OrderedDict

from graphene.utils.subclass_with_meta import SubclassWithMeta_Meta

from ..pyutils.compat import Enum as PyEnum
from .base import BaseOptions, BaseType
from .unmountedtype import UnmountedType


def eq_enum(self, other):
    if isinstance(other, self.__class__):
        return self is other
    return self.value is other


EnumType = type(PyEnum)


class EnumOptions(BaseOptions):
    enum = None  # type: Enum
    deprecation_reason = None


class EnumMeta(SubclassWithMeta_Meta):
    def __new__(cls, name, bases, classdict, **options):
        enum_members = OrderedDict(classdict, __eq__=eq_enum)
        # We remove the Meta attribute from the class to not collide
        # with the enum values.
        enum_members.pop("Meta", None)
        enum = PyEnum(cls.__name__, enum_members)
        return SubclassWithMeta_Meta.__new__(
            cls, name, bases, OrderedDict(classdict, __enum__=enum), **options
        )

    def get(cls, value):
        return cls._meta.enum(value)

    def __getitem__(cls, value):
        return cls._meta.enum[value]

    def __prepare__(name, bases, **kwargs):  # noqa: N805
        return OrderedDict()

    def __call__(cls, *args, **kwargs):  # noqa: N805
        if cls is Enum:
            description = kwargs.pop("description", None)
            deprecation_reason = kwargs.pop("deprecation_reason", None)
            return cls.from_enum(
                PyEnum(*args, **kwargs),
                description=description,
                deprecation_reason=deprecation_reason,
            )
        return super().__call__(*args, **kwargs)
        # return cls._meta.enum(*args, **kwargs)

    def from_enum(cls, enum, description=None, deprecation_reason=None):  # noqa: N805
        description = description or enum.__doc__
        meta_dict = {
            "enum": enum,
            "description": description,
            "deprecation_reason": deprecation_reason,
        }
        meta_class = type("Meta", (object,), meta_dict)
        return type(meta_class.enum.__name__, (Enum,), {"Meta": meta_class})


class Enum(UnmountedType, BaseType, metaclass=EnumMeta):
    """
    Enum type definition

    Defines a static set of values that can be provided as a Field, Argument or InputField.

    .. code:: python

        from graphene import Enum

        class NameFormat(Enum):
            FIRST_LAST = "first_last"
            LAST_FIRST = "last_first"

    Meta:
        enum (optional, Enum): Python enum to use as a base for GraphQL Enum.

        name (optional, str): Name of the GraphQL type (must be unique in schema). Defaults to class
            name.
        description (optional, str): Description of the GraphQL type in the schema. Defaults to class
            docstring.
        deprecation_reason (optional, str): Setting this value indicates that the enum is
            depreciated and may provide instruction or reason on how for clients to proceed.
    """

    @classmethod
    def __init_subclass_with_meta__(cls, enum=None, _meta=None, **options):
        if not _meta:
            _meta = EnumOptions(cls)
        _meta.enum = enum or cls.__enum__
        _meta.deprecation_reason = options.pop("deprecation_reason", None)
        for key, value in _meta.enum.__members__.items():
            setattr(cls, key, value)

        super().__init_subclass_with_meta__(_meta=_meta, **options)

    @classmethod
    def get_type(cls):
        """
        This function is called when the unmounted type (Enum instance)
        is mounted (as a Field, InputField or Argument)
        """
        return cls
