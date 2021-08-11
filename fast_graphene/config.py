from datetime import date
from datetime import datetime
from decimal import Decimal as decimal

from graphene.types import Boolean
from graphene.types import Date
from graphene.types import DateTime
from graphene.types import Decimal
from graphene.types import Float
from graphene.types import Int
from graphene.types import String

SCALAR_MAP = {
    int: Int,
    float: Float,
    str: String,
    decimal: Decimal,
    date: Date,
    datetime: DateTime,
    bool: Boolean,
}

TYPE_MAP = {}
