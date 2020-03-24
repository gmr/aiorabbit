import datetime
import decimal
import typing


FieldArray = typing.List['FieldValue']
"""A data structure for holding an array of field values."""

FieldTable = typing.Dict[str, 'FieldValue']
"""Field tables are data structures that contain packed name-value pairs.

The name-value pairs are encoded as short string defining the name, and octet
defining the values type and then the value itself. The valid field types for
tables are an extension of the native integer, bit, string, and timestamp
types, and are shown in the grammar. Multi-octet integer fields are always
held in network byte order.

"""

FieldValue = typing.Union[bool,
                          bytearray,
                          decimal.Decimal,
                          FieldArray,
                          FieldTable,
                          float,
                          int,
                          None,
                          str,
                          datetime.datetime]
"""Defines valid field values for a :const:`FieldTable` and a
:const:`FieldValue`

"""

Arguments = typing.Optional[FieldTable]
"""Defines an AMQP method arguments argument data type"""
