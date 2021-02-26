# Credit: https://github.com/MinaProtocol/coda-python-client

from enum import Enum


class CurrencyFormat(Enum):
    """An Enum representing different formats of Currency in coda.

  Constants:
      WHOLE - represents whole coda (1 whole coda == 10^9 nanocodas)
      NANO - represents the atomic unit of coda
  """
    WHOLE = 1
    NANO = 2


class CurrencyUnderflow(Exception):
    pass


class Currency():
    """A convenience wrapper around interacting with coda currency values.

  This class supports performing math on Currency values of differing formats.
  Currency instances can be added or subtracted. Currency instances can also be
  scaled through multiplication (either against another Currency instance or a
  int scalar).
  """
    @classmethod
    def __nanocodas_from_int(_cls, n):
        return n * 1000000000

    @classmethod
    def __nanocodas_from_string(_cls, s):
        segments = s.split('.')
        if len(segments) == 1:
            return int(segments[0])
        elif len(segments) == 2:
            [l, r] = segments
            if len(r) <= 9:
                return int(l + r + ('0' * (9 - len(r))))
            else:
                raise Exception('invalid coda currency format: %s' % s)

    def __init__(self, value, format=CurrencyFormat.WHOLE):
        """Constructs a new Currency instance. Values of different CurrencyFormats may be passed in to construct the instance.

    Arguments:
        value {int|float|string} - The value to construct the Currency instance from
        format {CurrencyFormat} - The representation format of the value

    Return:
        Currency - The newly constructed Currency instance

    In the case of format=CurrencyFormat.WHOLE, then it is interpreted as value * 10^9 nanocodas.
    In the case of format=CurrencyFormat.NANO, value is only allowed to be an int, as there can be no decimal point for nanocodas.
    """
        if format == CurrencyFormat.WHOLE:
            if isinstance(value, int):
                self.__nanocodas = Currency.__nanocodas_from_int(value)
            elif isinstance(value, float):
                self.__nanocodas = Currency.__nanocodas_from_string(str(value))
            elif isinstance(value, str):
                self.__nanocodas = Currency.__nanocodas_from_string(value)
            else:
                raise Exception('cannot construct whole Currency from %s' %
                                type(value))
        elif format == CurrencyFormat.NANO:
            if isinstance(value, int):
                self.__nanocodas = value
            else:
                raise Exception('cannot construct nano Currency from %s' %
                                type(value))
        else:
            raise Exception('invalid Currency format %s' % format)

    def decimal_format(self):
        """Computes the string decimal format representation of a Currency instance.

    Return:
        str - The decimal format representation of the Currency instance
    """
        s = str(self.__nanocodas)
        if len(s) > 9:
            return s[:-9] + '.' + s[-9:]
        else:
            return '0.' + ('0' * (9 - len(s))) + s

    def nanocodas(self):
        """Accesses the raw nanocodas representation of a Currency instance.

    Return:
        int - The nanocodas of the Currency instance represented as an integer
    """
        return self.__nanocodas

    def __str__(self):
        return self.decimal_format()

    def __repr__(self):
        return 'Currency(%s)' % self.decimal_format()

    def __add__(self, other):
        if isinstance(other, Currency):
            return Currency(self.nanocodas() + other.nanocodas(),
                            format=CurrencyFormat.NANO)
        else:
            raise Exception('cannot add Currency and %s' % type(other))

    def __sub__(self, other):
        if isinstance(other, Currency):
            new_value = self.nanocodas() - other.nanocodas()
            if new_value >= 0:
                return Currency(new_value, format=CurrencyFormat.NANO)
            else:
                raise CurrencyUnderflow()
        else:
            raise Exception('cannot subtract Currency and %s' % type(other))

    def __mul__(self, other):
        if isinstance(other, int):
            return Currency(self.nanocodas() * other,
                            format=CurrencyFormat.NANO)
        elif isinstance(other, Currency):
            return Currency(self.nanocodas() * other.nanocodas(),
                            format=CurrencyFormat.NANO)
        else:
            raise Exception('cannot multiply Currency and %s' % type(other))
