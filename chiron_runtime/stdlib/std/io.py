# Imports needed by: PySimpleValidate
from __future__ import absolute_import, division, print_function

import calendar
import datetime
import re
import sys
import time

from typing import Union, Pattern, Type, Dict, Tuple, Optional, Sequence, Any, List, overload, override

import getpass

import builtins

__all__ = [
    'PyInputPlusException',
    'PySimpleValidateException',
    'RetryLimitException',
    'TimeoutException',
    'ValidationException',
    'inputAddress',
    'inputBool',
    'inputChoice',
    'inputCustom',
    'inputDate',
    'inputDatetime',
    'inputDayOfMonth',
    'inputDayOfWeek',
    'inputEmail',
    'inputFilename',
    'inputFilepath',
    'inputFloat',
    'inputIP',
    'inputInt',
    'inputMenu',
    'inputMonth',
    'inputName',
    'inputNum',
    'inputPassword',
    'inputPhone',
    'inputRegex',
    'inputRegexStr',
    'inputStr',
    'inputTime',
    'inputURL',
    'inputUSState',
    'inputYesNo',
    'inputZip',
    'input',
    'print',
    'validateAddress',
    'validateBool',
    'validateChoice',
    'validateDate',
    'validateDatetime',
    'validateDayOfMonth',
    'validateDayOfWeek',
    'validateEmail',
    'validateFilename',
    'validateFilepath',
    'validateFloat',
    'validateIP',
    'validateIPv4',
    'validateIPv6',
    'validateInt',
    'validateMonth',
    'validateName',
    'validateNum',
    'validatePhone',
    'validateRegex',
    'validateRegexStr',
    'validateStr',
    'validateTime',
    'validateURL',
    'validateUSState',
    'validateYesNo',
]

def print(*args):
    """
    Chiron std.io.print: alias di print Python
    """
    # Converte tutto in stringa e stampa separato da spazio
    builtins.print(*args)

def input(prompt: str = "") -> str:
    """
    Chiron std.io.input: alias di input Python
    """
    return builtins.input(prompt)

"""
PySimpleValidate
"""

RE_PATTERN_TYPE = type(re.compile(""))

if sys.version_info >= (3, 3):
    import collections.abc

    SEQUENCE_ABC = collections.abc.Sequence

MAX_ERROR_STR_LEN: int = 50 # Used by _errstr():

IPV4_REGEX: Pattern = re.compile(r"""((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)(\.|$)){4}""") # From https://stackoverflow.com/a/5284410/1893164
IPV6_REGEX: Pattern = re.compile(
    r"""(
([0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|          # 1:2:3:4:5:6:7:8
([0-9a-fA-F]{1,4}:){1,7}:|                         # 1::                              1:2:3:4:5:6:7::
([0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|         # 1::8             1:2:3:4:5:6::8  1:2:3:4:5:6::8
([0-9a-fA-F]{1,4}:){1,5}(:[0-9a-fA-F]{1,4}){1,2}|  # 1::7:8           1:2:3:4:5::7:8  1:2:3:4:5::8
([0-9a-fA-F]{1,4}:){1,4}(:[0-9a-fA-F]{1,4}){1,3}|  # 1::6:7:8         1:2:3:4::6:7:8  1:2:3:4::8
([0-9a-fA-F]{1,4}:){1,3}(:[0-9a-fA-F]{1,4}){1,4}|  # 1::5:6:7:8       1:2:3::5:6:7:8  1:2:3::8
([0-9a-fA-F]{1,4}:){1,2}(:[0-9a-fA-F]{1,4}){1,5}|  # 1::4:5:6:7:8     1:2::4:5:6:7:8  1:2::8
[0-9a-fA-F]{1,4}:((:[0-9a-fA-F]{1,4}){1,6})|       # 1::3:4:5:6:7:8   1::3:4:5:6:7:8  1::8
:((:[0-9a-fA-F]{1,4}){1,7}|:)|                     # ::2:3:4:5:6:7:8  ::2:3:4:5:6:7:8 ::8       ::
fe80:(:[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}|     # fe80::7:8%eth0   fe80::7:8%1     (link-local IPv6 addresses with zone index)
::(ffff(:0{1,4}){0,1}:){0,1}
((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}
(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])|          # ::255.255.255.255   ::ffff:255.255.255.255  ::ffff:0:255.255.255.255  (IPv4-mapped IPv6 addresses and IPv4-translated addresses)
([0-9a-fA-F]{1,4}:){1,4}:
((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}
(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])           # 2001:db8:3:4::192.0.2.33  64:ff9b::192.0.2.33 (IPv4-Embedded IPv6 Address)
)""",
    re.VERBOSE,
) # From https://stackoverflow.com/a/17871737/1893164

REGEX_TYPE: Type = type(IPV4_REGEX)

URL_REGEX: Pattern   = re.compile(r"""(http(s)?:\/\/.)?(www\.)?[-a-zA-Z0-9@:%._\+~#=]{2,256}\.[a-z]{2,6}\b([-a-zA-Z0-9@:%_\+.~#?&//=]*)""")
EMAIL_REGEX: Pattern = re.compile(r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)") # https://emailregex.com/

USA_STATES: Dict[str, str] = {
    "AL": "Alabama",
    "AK": "Alaska",
    "AZ": "Arizona",
    "AR": "Arkansas",
    "CA": "California",
    "CO": "Colorado",
    "CT": "Connecticut",
    "DE": "Delaware",
    "FL": "Florida",
    "GA": "Georgia",
    "HI": "Hawaii",
    "ID": "Idaho",
    "IL": "Illinois",
    "IN": "Indiana",
    "IA": "Iowa",
    "KS": "Kansas",
    "KY": "Kentucky",
    "LA": "Louisiana",
    "ME": "Maine",
    "MD": "Maryland",
    "MA": "Massachusetts",
    "MI": "Michigan",
    "MN": "Minnesota",
    "MS": "Mississippi",
    "MO": "Missouri",
    "MT": "Montana",
    "NE": "Nebraska",
    "NV": "Nevada",
    "NH": "New Hampshire",
    "NJ": "New Jersey",
    "NM": "New Mexico",
    "NY": "New York",
    "NC": "North Carolina",
    "ND": "North Dakota",
    "OH": "Ohio",
    "OK": "Oklahoma",
    "OR": "Oregon",
    "PA": "Pennsylvania",
    "RI": "Rhode Island",
    "SC": "South Carolina",
    "SD": "South Dakota",
    "TN": "Tennessee",
    "TX": "Texas",
    "UT": "Utah",
    "VT": "Vermont",
    "VA": "Virginia",
    "WA": "Washington",
    "WV": "West Virginia",
    "WI": "Wisconsin",
    "WY": "Wyoming",
}
USA_STATES_REVERSED: Dict[str, str] = dict([(USA_STATES[abbrev], abbrev) for abbrev in USA_STATES.keys()])
USA_STATES_UPPER: Dict[str, str] = dict([(abbrev, USA_STATES[abbrev].upper()) for abbrev in USA_STATES.keys()])

ENGLISH_MONTHS: Dict[str, str] = {
    "JAN": "January",
    "FEB": "February",
    "MAR": "March",
    "APR": "April",
    "MAY": "May",
    "JUN": "June",
    "JUL": "July",
    "AUG": "August",
    "SEP": "September",
    "OCT": "October",
    "NOV": "November",
    "DEC": "December",
}
ENGLISH_MONTH_NAMES: Tuple[str, str, str, str, str, str, str, str, str, str, str, str] = (
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
)
ENGLISH_DAYS_OF_WEEK: Dict[str, str] = {
    "SUN": "Sunday",
    "MON": "Monday",
    "TUE": "Tuesday",
    "WED": "Wednesday",
    "THU": "Thursday",
    "FRI": "Friday",
    "SAT": "Saturday",
}
DEFAULT_BLOCKLIST_RESPONSE: str = "This response is invalid."

SUBSTITUTE_PARAMETERS: list[str] = [
    "%%",
    "%%f",
    "%%s",
    "%%e"
]

class PySimpleValidateException(Exception):
    """Base class for exceptions raised when PySimpleValidate functions are misused.
    This doesn't represent a validation failure."""

    pass

class ValidationException(Exception):
    """Raised when a validation function fails to validate the value."""

    pass


class PyInputPlusException(Exception):

    pass

class ValidationException(PyInputPlusException):

    pass

class TimeoutException(Exception):

    pass

class RetryLimitException(Exception):

    pass


def _errstr(value):
    # type: (str) -> str

    # We won't make the caller convert value to a string each time.
    value = str(value)
    if len(value) > MAX_ERROR_STR_LEN:
        return value[:MAX_ERROR_STR_LEN] + "..."
    else:
        return value


def _getStrippedValue(value, strip):
    # type: (str, Union[None, str, bool]) -> str

    if strip is None:
        value = value.strip()  # Call strip() with no arguments to strip whitespace.
    elif isinstance(strip, str):
        value = value.strip(strip)  # Call strip(), passing the strip argument.
    elif strip is False:
        pass  # Don't strip anything.
    return value


def _raiseValidationException(standardExcMsg, customExcMsg=None, values=[], exception=None):
    # type: (str, Optional[str]) -> None
    """Raise ValidationException with standardExcMsg, unless customExcMsg is specified."""
    if customExcMsg is None:
        raise ValidationException(str(standardExcMsg))
    else:
        finalMsg = customExcMsg
        #replace all the placeholders with the given values
        for i, value in enumerate(values):
            finalMsg = finalMsg.replace(SUBSTITUTE_PARAMETERS[i], value)

        if exception: finalMsg = finalMsg.replace("%%e", exception)

        #if there weren't values for the placeholders, just remove them
        for i in range(len(SUBSTITUTE_PARAMETERS)):
            finalMsg = finalMsg.replace(SUBSTITUTE_PARAMETERS[i], '')

        raise ValidationException(str(finalMsg))


def _prevalidationCheck(value, blank, strip, allowRegexes, blockRegexes, whiteList=None, blackList=None, excMsg=None):
    # type: (str, bool, Union[None, str, bool], Union[None, Sequence[Union[Pattern, str]]], Union[None, Sequence[Union[Pattern, str, Sequence[Union[Pattern, str]]]]], Optional[str]) -> Tuple[bool, str]
    """Returns a tuple of two values: the first is a bool that tells the caller
    if they should immediately return True, the second is a new, possibly stripped
    value to replace the value passed for value parameter.

    We'd want the caller immediately return value in some cases where further
    validation isn't needed, such as if value is blank and blanks are
    allowed, or if value matches an allowlist or blocklist regex.

    This function is called by the validate*() functions to perform some common
    housekeeping."""

    # TODO - add a allowlistFirst and blocklistFirst to determine which is checked first. (Right now it's allowlist)

    value = str(value)

    # Optionally strip whitespace or other characters from value.
    value = _getStrippedValue(value, strip)

    # Validate for blank values.
    if not blank and value == "":
        # value is blank but blanks aren't allowed.
        _raiseValidationException(("Blank values are not allowed."), excMsg)
    elif blank and value == "":
        return (
            True,
            value,
        )  # The value is blank and blanks are allowed, so return True to indicate that the caller should return value immediately.

    # NOTE: We check if something matches the allow-list first, then we check the block-list second.

    # NOTE: The same logic is applied to the white-list and black-list, except they are checked first

    # Check the whiteList.
    if whiteList is not None:
        for allowElement in whiteList:
            if value in allowElement:
                return (
                    True,
                    value,
                )  # The value is in the allowlist, so return True to indicate that the caller should return value immediately.

    # Check the blackList.
    if blackList is not None:
        for blockElement in blackList:
            if value in blockElement:
                _raiseValidationException('The value is in a black-list', excMsg, [value])  # value is on a blocklist

    # Check the allowRegexes.
    if allowRegexes is not None:
        for allowRegex in allowRegexes:
            if isinstance(allowRegex, RE_PATTERN_TYPE):
                if allowRegex.search(value) is not None:
                    return (
                        True,
                        value,
                    )  # The value is in the allowlist, so return True to indicate that the caller should return value immediately.
            else:
                if re.search(allowRegex, value) is not None:
                    return (
                        True,
                        value,
                    )  # The value is in the allowlist, so return True to indicate that the caller should return value immediately.

    # Check the blockRegexes.
    if blockRegexes is not None:
        for blocklistRegexItem in blockRegexes:
            if isinstance(blocklistRegexItem, (str, RE_PATTERN_TYPE)):
                regex, response = blocklistRegexItem, DEFAULT_BLOCKLIST_RESPONSE
            else:
                # NOTE: blockRegexes is potentially so many types at runtime, so ignore the type hint error on this next line:
                regex, response = blocklistRegexItem  # type: ignore

            if isinstance(regex, RE_PATTERN_TYPE) and regex.search(value) is not None:
                _raiseValidationException(response, excMsg, [value])  # value is on a blocklist
            elif re.search(regex, value) is not None:
                _raiseValidationException(response, excMsg, [value])  # value is on a blocklist

    return (
        False,
        value,
    )  # Return False and the possibly modified value, and leave it up to the caller to decide if it's valid or not.


def _validateGenericParameters(blank, strip, allowRegexes, blockRegexes):
    # type: (bool, Union[None, str, bool], Union[None, Sequence[Union[Pattern, str]]], Union[None, Sequence[Union[Pattern, str, Sequence[Union[Pattern, str]]]]]) -> None
    """Returns None if the blank, strip, and blockRegexes parameters are valid
    of PySimpleValidate's validation functions have. Raises a PySimpleValidateException
    if any of the arguments are invalid."""

    # Check blank parameter.
    if not isinstance(blank, bool):
        raise PySimpleValidateException("blank argument must be a bool")

    # Check strip parameter.
    if not isinstance(strip, (bool, str, type(None))):
        raise PySimpleValidateException("strip argument must be a bool, None, or str")

    # Check allowRegexes parameter (including each regex in it).
    if allowRegexes is None:
        allowRegexes = []  # allowRegexes defaults to a blank list.

    if not isinstance(allowRegexes, SEQUENCE_ABC):
        raise PySimpleValidateException("allowRegexes must be a sequence of regex_strs")

    for allowRegex in allowRegexes:
        if not isinstance(allowRegex, (str, RE_PATTERN_TYPE)):
            raise PySimpleValidateException("items in allowRegexes must be a regex pattern or regex str")

    # Check allowRegexes parameter (including each regex in it).
    # NOTE: blockRegexes is NOT the same format as allowlistRegex, it can
    # include an "invalid input reason" string to display if the input matches
    # the blocklist regex.
    if blockRegexes is None:
        blockRegexes = []  # blockRegexes defaults to a blank list.

    if not isinstance(blockRegexes, SEQUENCE_ABC):
        raise PySimpleValidateException(
            "blockRegexes must be a pattern, regex str, or sequence of (pattern, regex str) tuples"
        )
    for blockRegex in blockRegexes:
        if isinstance(blockRegex, (str, RE_PATTERN_TYPE)):
            continue
        # NOTE: blockRegex is potentially so many types at runtime, so ignore the type hint error on this next line:
        if len(blockRegex) != 2:  # type: ignore
            raise PySimpleValidateException(
                "blockRegexes must be a pattern, regex str, or sequence of (pattern, regex str) tuples"
            )
        if not isinstance(blockRegex[0], str) or not isinstance(blockRegex[1], str):  # type: ignore
            raise PySimpleValidateException(
                "blockRegexes must be a pattern, regex str, or sequence of (pattern, regex str) tuples"
            )


def _validateParamsFor_validateNum(min=None, max=None, lessThan=None, greaterThan=None):
    # type: (Union[int, float, None], Union[int, float, None], Union[int, float, None], Union[int, float, None]) -> None
    """Raises an exception if the arguments are invalid. This is called by
    the validateNum(), validateInt(), and validateFloat() functions to
    check its arguments. This code was refactored out to a separate function
    so that the PyInputPlus module (or other modules) could check their
    parameters' arguments for inputNum() etc.
    """

    if (min is not None) and (greaterThan is not None):
        raise PySimpleValidateException("only one argument for min or greaterThan can be passed, not both")
    if (max is not None) and (lessThan is not None):
        raise PySimpleValidateException("only one argument for max or lessThan can be passed, not both")

    if (min is not None) and (max is not None) and (min > max):
        raise PySimpleValidateException("the min argument must be less than or equal to the max argument")
    if (min is not None) and (lessThan is not None) and (min >= lessThan):
        raise PySimpleValidateException("the min argument must be less than the lessThan argument")
    if (max is not None) and (greaterThan is not None) and (max <= greaterThan):
        raise PySimpleValidateException("the max argument must be greater than the greaterThan argument")

    for name, val in (("min", min), ("max", max), ("lessThan", lessThan), ("greaterThan", greaterThan)):
        if not isinstance(val, (int, float, type(None))):
            raise PySimpleValidateException(name + " argument must be int, float, or NoneType")


def validateStr(value, blank=False, strip=None, allowRegexes=None, blockRegexes=None, whiteList=None, blackList=None, excMsg=None):
    # type: (str, bool, Union[None, str, bool], Union[None, Sequence[Union[Pattern, str]]], Union[None, Sequence[Union[Pattern, str, Sequence[Union[Pattern, str]]]]], Optional[str]) -> str


    # Validate parameters.
    _validateGenericParameters(blank=blank, strip=strip, allowRegexes=None, blockRegexes=blockRegexes)
    returnNow, value = _prevalidationCheck(value, blank, strip, allowRegexes, blockRegexes, whiteList, blackList, excMsg)

    return value


def validateNum(
    value,
    blank=False,
    strip=None,
    allowRegexes=None,
    blockRegexes=None,
    whiteList=None,
    blackList=None,
    _numType="num",
    min=None,
    max=None,
    lessThan=None,
    greaterThan=None,
    excMsg=None,
):
    # type: (str, bool, Union[None, str, bool], Union[None, Sequence[Union[Pattern, str]]], Union[None, Sequence[Union[Pattern, str, Sequence[Union[Pattern, str]]]]], str, Optional[int], Optional[int], Optional[int], Optional[int], Optional[str]) -> Union[int, float, str]


    # TODO - Add notes to the documentation that the parameters (except value) should all be passed using keyword arguments.

    assert _numType in ("num", "int", "float")

    # Validate parameters.
    _validateGenericParameters(blank=blank, strip=strip, allowRegexes=None, blockRegexes=blockRegexes)
    _validateParamsFor_validateNum(min=min, max=max, lessThan=lessThan, greaterThan=greaterThan)

    returnNow, value = _prevalidationCheck(value, blank, strip, allowRegexes, blockRegexes, whiteList, blackList, excMsg)
    if returnNow:
        # If we can convert value to an int/float, then do so. For example,
        # if an allowlist regex allows '42', then we should return 42 or 42.0.
        if (_numType == "num" and "." in value) or (_numType == "float"):
            try:
                return float(value)
            except ValueError:
                return value  # Return the value as is.
        elif (_numType == "num" and "." not in value) or (_numType == "int"):
            try:
                return int(value)
            except ValueError:
                return value  # Return the value as is.
        else:
            assert False  # This branch should never happen.

    # Validate the value's type (and convert value back to a number type).
    if _numType == "num" and "." in value:
        # We are expecting a "num" (float or int) type and the user entered a float.
        try:
            numericValue = float(value)  # type: Union[int, float]
        except:
            _raiseValidationException(("%r is not a number.") % (_errstr(value)), excMsg, [value])
    elif _numType == "num" and "." not in value:
        # We are expecting a "num" (float or int) type and the user entered an int.
        try:
            numericValue = int(value)
        except:
            _raiseValidationException(("%r is not a number.") % (_errstr(value)), excMsg, [value])
    elif _numType == "float":
        try:
            numericValue = float(value)
        except:
            _raiseValidationException(("%r is not a float.") % (_errstr(value)), excMsg, [value])
    elif _numType == "int":
        try:
            if float(value) % 1 != 0:
                # The number is a float that doesn't end with ".0"
                _raiseValidationException(("%r is not an integer.") % (_errstr(value)), excMsg, [value])
            numericValue = int(float(value))
        except:
            _raiseValidationException(("%r is not an integer.") % (_errstr(value)), excMsg, [value])
    else:
        assert False  # This branch should never happen.

    # Validate against min argument.
    if min is not None and numericValue < min:
        _raiseValidationException(("Number must be at minimum %s.") % (min, ), excMsg, [value])

    # Validate against max argument.
    if max is not None and numericValue > max:
        _raiseValidationException(("Number must be at maximum %s.") % (max, ), excMsg, [value])

    # Validate against max argument.
    if lessThan is not None and numericValue >= lessThan:
        _raiseValidationException(("Number must be less than %s.") % (lessThan, ), excMsg, [value])

    # Validate against max argument.
    if greaterThan is not None and numericValue <= greaterThan:
        _raiseValidationException(("Number must be greater than %s.") % (greaterThan, ), excMsg, [value])

    return numericValue


def validateInt(
    value,
    blank=False,
    strip=None,
    allowRegexes=None,
    blockRegexes=None,
    whiteList=None,
    blackList=None,
    min=None,
    max=None,
    lessThan=None,
    greaterThan=None,
    excMsg=None,
):
    # type: (str, bool, Union[None, str, bool], Union[None, Sequence[Union[Pattern, str]]], Union[None, Sequence[Union[Pattern, str, Sequence[Union[Pattern, str]]]]], Optional[int], Optional[int], Optional[int], Optional[int], Optional[str]) -> Union[int, str]


    # Even though validateNum *could* return a float, it won't if _numType is 'int', so ignore mypy's complaint:
    return validateNum(
        value=value,
        blank=blank,
        strip=strip,
        allowRegexes=allowRegexes,  # type: ignore
        blockRegexes=blockRegexes,
        whiteList=whiteList,
        blackList=blackList,
        _numType="int",
        min=min,
        max=max,
        lessThan=lessThan,
        greaterThan=greaterThan,
        excMsg=excMsg
    )


def validateFloat(
    value,
    blank=False,
    strip=None,
    allowRegexes=None,
    blockRegexes=None,
    whiteList=None,
    blackList=None,
    min=None,
    max=None,
    lessThan=None,
    greaterThan=None,
    excMsg=None,
):
    # type: (str, bool, Union[None, str, bool], Union[None, Sequence[Union[Pattern, str]]], Union[None, Sequence[Union[Pattern, str, Sequence[Union[Pattern, str]]]]], Optional[int], Optional[int], Optional[int], Optional[int], Optional[str]) -> Union[float, str]


    # Even though validateNum *could* return a int, it won't if _numType is 'float', so ignore mypy's complaint:
    return validateNum(
        value=value,
        blank=blank,
        strip=strip,
        allowRegexes=allowRegexes,
        blockRegexes=blockRegexes,
        whiteList=whiteList,
        blackList=blackList,
        _numType="float",
        min=min,
        max=max,
        lessThan=lessThan,
        greaterThan=greaterThan,
        excMsg=excMsg
    )


def _validateParamsFor_validateChoice(
    choices,
    blank=False,
    strip=None,
    blockRegexes=None,
    numbered=False,
    lettered=False,
    caseSensitive=False,
):
    # type: (Sequence[Any], bool, Union[None, str, bool], Union[None, Sequence[Union[Pattern, str]]], Union[None, Sequence[Union[Pattern, str, Sequence[Union[Pattern, str]]]]], bool, bool, bool, Optional[str]) -> None
    """Raises PySimpleValidateException if the arguments are invalid. This is called by
    the validateChoice() function to check its arguments. This code was
    refactored out to a separate function so that the PyInputPlus module (or
    other modules) could check their parameters' arguments for inputChoice().
    """

    if not isinstance(caseSensitive, bool):
        raise PySimpleValidateException("caseSensitive argument must be a bool")

    if not isinstance(choices, SEQUENCE_ABC):
        raise PySimpleValidateException("choices arg must be a sequence")

    try:
        len(choices)
    except:
        raise PySimpleValidateException("choices arg must be a sequence")
    if blank == False and len(choices) < 2:
        raise PySimpleValidateException("choices must have at least two items if blank is False")
    elif blank == True and len(choices) < 1:
        raise PySimpleValidateException("choices must have at least one item")

    _validateGenericParameters(blank=blank, strip=strip, allowRegexes=None, blockRegexes=blockRegexes)

    if lettered and len(choices) > 26:
        raise PySimpleValidateException("lettered argument cannot be True if there are more than 26 choices")
    if numbered and lettered:
        raise PySimpleValidateException("numbered and lettered arguments cannot both be True")

    if len(choices) != len(set(choices)):
        raise PySimpleValidateException("duplicate entries in choices argument")

    if not caseSensitive and len(choices) != len(set([choice.upper() for choice in choices])):
        raise PySimpleValidateException("duplicate case-insensitive entries in choices argument")


def validateChoice(
    value,
    choices,
    blank=False,
    strip=None,
    allowRegexes=None,
    blockRegexes=None,
    whiteList=None,
    blackList=None,
    numbered=False,
    lettered=False,
    caseSensitive=False,
    excMsg=None,
):
    # type: (str, Sequence[Any], bool, Union[None, str, bool], Union[None, Sequence[Union[Pattern, str]]], Union[None, Sequence[Union[Pattern, str, Sequence[Union[Pattern, str]]]]], bool, bool, bool, Optional[str]) -> str


    # Validate parameters.
    _validateParamsFor_validateChoice(
        choices=choices,
        blank=blank,
        strip=strip,
        blockRegexes=blockRegexes,
        numbered=numbered,
        lettered=lettered,
        caseSensitive=caseSensitive,
    )

    strChoices = []  # type: List[str]
    for choice in choices:
        strChoices.append(str(choice))

    if "" in strChoices:
        # blank needs to be set to True here, otherwise '' won't be accepted as a choice.
        blank = True

    returnNow, value = _prevalidationCheck(value, blank, strip, allowRegexes, blockRegexes, whiteList, blackList, excMsg)
    if returnNow:
        return value

    # Validate against strChoices.
    if value in strChoices:
        return value
    if numbered and value.isdigit() and 0 < int(value) <= len(strChoices):  # value must be 1 to len(strChoices)
        # Numbered options begins at 1, not 0.
        return strChoices[
            int(value) - 1
        ]  # -1 because the numbers are 1 to len(strChoices) but the index are 0 to len(strChoices) - 1
    if lettered and len(value) == 1 and value.isalpha() and 0 < ord(value.upper()) - 64 <= len(strChoices):
        # Lettered options are always case-insensitive.
        return strChoices[ord(value.upper()) - 65]
    if not caseSensitive and value.upper() in [choice.upper() for choice in strChoices]:
        # Return the original item in strChoices that value has a case-insensitive match with.
        return strChoices[[choice.upper() for choice in strChoices].index(value.upper())]

    _raiseValidationException(("%r is not a valid choice.") % (_errstr(value)), excMsg, [value])
    assert False, "The execution reached this point, even though the previous line should have raised an exception."


def _validateParamsFor__validateToDateTimeFormat(
    formats, blank=False, strip=None, allowRegexes=None, blockRegexes=None
):
    # type: (Union[str, Sequence[str]], bool, Union[None, str, bool], Union[None, Sequence[Union[Pattern, str]]], Union[None, Sequence[Union[Pattern, str, Sequence[Union[Pattern, str]]]]], Optional[str]) -> None
    """Raises PySimpleValidateException if the arguments are invalid. This is called by
    the validateTime() function to check its arguments. This code was
    refactored out to a separate function so that the PyInputPlus module (or
    other modules) could check their parameters' arguments for inputTime().
    """
    _validateGenericParameters(blank=blank, strip=strip, allowRegexes=allowRegexes, blockRegexes=blockRegexes)
    if formats is None:
        raise PySimpleValidateException("formats parameter must be specified")

    if isinstance(formats, str):
        raise PySimpleValidateException("formats argument must be a non-str sequence of strftime format strings")

    if not isinstance(formats, SEQUENCE_ABC):
        raise PySimpleValidateException("formats argument must be a non-str sequence of strftime format strings")

    for timeFormat in formats:  # "format" name is used by the built-in format() function, so we use timeFormat instead.
        try:
            time.strftime(timeFormat)  # This will raise an exception if the format is invalid.
        except:
            raise PySimpleValidateException("formats argument contains invalid strftime format strings")


def _validateToDateTimeFormat(
    value, formats, blank=False, strip=None, allowRegexes=None, blockRegexes=None, whiteList=None, blackList=None, excMsg=None
):
    # type: (str, Union[str, Sequence[str]], bool, Union[None, str, bool], Union[None, Sequence[Union[Pattern, str]]], Union[None, Sequence[Union[Pattern, str, Sequence[Union[Pattern, str]]]]], Optional[str]) -> Union[datetime.datetime, str]
    # Validate parameters.
    _validateParamsFor__validateToDateTimeFormat(
        formats, blank=blank, strip=strip, allowRegexes=allowRegexes, blockRegexes=blockRegexes
    )

    if isinstance(formats, str):
        # Ensure that `formats` is always a sequence of strings:
        formats = [formats]

    returnNow, value = _prevalidationCheck(value, blank, strip, allowRegexes, blockRegexes, whiteList, blackList, excMsg)
    if returnNow:
        for timeFormat in formats:
            # If value can be converted to a datetime object, convert it.
            try:
                return datetime.datetime.strptime(value, timeFormat)
            except ValueError:
                continue  # If this format fails to parse, move on to the next format.
        return value  # Return the value as is.

    # Validate against the given formats.
    for timeFormat in formats:
        try:
            return datetime.datetime.strptime(value, timeFormat)
        except ValueError:
            continue  # If this format fails to parse, move on to the next format.

    _raiseValidationException(("%r is not a valid time.") % (value, ), excMsg, [value])
    assert False, "The execution reached this point, even though the previous line should have raised an exception."


def validateTime(
    value,
    formats=("%H:%M:%S", "%H:%M", "%X"),
    blank=False,
    strip=None,
    allowRegexes=None,
    blockRegexes=None,
    whiteList=None,
    blackList=None,
    excMsg=None,
):
    # type: (str, Union[str, Sequence[str]], bool, Union[None, str, bool], Union[None, Sequence[Union[Pattern, str]]], Union[None, Sequence[Union[Pattern, str, Sequence[Union[Pattern, str]]]]], Optional[str]) -> Union[datetime.time, str]


    # TODO - handle this

    # Reuse the logic in _validateToDateTimeFormat() for this function.
    try:
        dt = _validateToDateTimeFormat(
            value, formats, blank=blank, strip=strip, allowRegexes=allowRegexes, blockRegexes=blockRegexes
        )
    except ValidationException:
        _raiseValidationException(("%r is not a valid time.") % (_errstr(value)), excMsg, [value])

    # `dt` could be a str if `value` matched one of the `allowRegexes`.
    if isinstance(dt, str):
        return dt  # Return the string value as-is.
    # At this point, dt is definitely a time object, so ignore mypy's complaints:
    return datetime.time(dt.hour, dt.minute, dt.second, dt.microsecond)  # type: ignore


def validateDate(
    value,
    formats=("%Y/%m/%d", "%y/%m/%d", "%m/%d/%Y", "%m/%d/%y", "%x"),
    blank=False,
    strip=None,
    allowRegexes=None,
    blockRegexes=None,
    whiteList=None,
    blackList=None,
    excMsg=None,
):
    # type: (str, Union[str, Sequence[str]], bool, Union[None, str, bool], Union[None, Sequence[Union[Pattern, str]]], Union[None, Sequence[Union[Pattern, str, Sequence[Union[Pattern, str]]]]], Optional[str]) -> Union[datetime.date, str]

    # Reuse the logic in _validateToDateTimeFormat() for this function.
    try:
        dt = _validateToDateTimeFormat(
            value, formats, blank=blank, strip=strip, allowRegexes=allowRegexes, blockRegexes=blockRegexes
        )
    except ValidationException:
        _raiseValidationException(("%r is not a valid date.") % (_errstr(value)), excMsg, [value])

    # `dt` could be a str if `value` matched one of the `allowRegexes`.
    if isinstance(dt, str):
        return dt  # Return the string value as-is.
    # At this point, dt is definitely a date object, so ignore mypy's complaints:
    return datetime.date(dt.year, dt.month, dt.day)  # type: ignore


def validateDatetime(
    value,
    formats=(
        "%Y/%m/%d %H:%M:%S",
        "%y/%m/%d %H:%M:%S",
        "%m/%d/%Y %H:%M:%S",
        "%m/%d/%y %H:%M:%S",
        "%x %H:%M:%S",  # type: ignore
        "%Y/%m/%d %H:%M",
        "%y/%m/%d %H:%M",
        "%m/%d/%Y %H:%M",
        "%m/%d/%y %H:%M",
        "%x %H:%M",
        "%Y/%m/%d %H:%M:%S",
        "%y/%m/%d %H:%M:%S",
        "%m/%d/%Y %H:%M:%S",
        "%m/%d/%y %H:%M:%S",
        "%x %H:%M:%S",
    ),
    blank=False,
    strip=None,
    allowRegexes=None,
    blockRegexes=None,
    whiteList=None,
    blackList=None,
    excMsg=None,
):
    # type: (str, Union[str, Sequence[str]], bool, Union[None, str, bool], Union[None, Sequence[Union[Pattern, str]]], Union[None, Sequence[Union[Pattern, str, Sequence[Union[Pattern, str]]]]], Optional[str]) -> Union[datetime.datetime, str]


    # Reuse the logic in _validateToDateTimeFormat() for this function.
    try:
        return _validateToDateTimeFormat(
            value, formats, blank=blank, strip=strip, allowRegexes=allowRegexes, blockRegexes=blockRegexes
        )
    except ValidationException:
        _raiseValidationException(("%r is not a valid date and time.") % (_errstr(value)), excMsg, [value])
    assert False, "The execution reached this point, even though the previous line should have raised an exception."


def validateFilename(value, blank=False, strip=None, allowRegexes=None, blockRegexes=None, whiteList=None, blackList=None, excMsg=None):
    # type: (str, bool, Union[None, str, bool], Union[None, Sequence[Union[Pattern, str]]], Union[None, Sequence[Union[Pattern, str, Sequence[Union[Pattern, str]]]]], Optional[str]) -> str


    # TODO: Did I capture the Linux/macOS invalid file characters too, or just Windows's?

    returnNow, value = _prevalidationCheck(value, blank, strip, allowRegexes, blockRegexes, whiteList, blackList, excMsg)
    if returnNow:
        return value

    if (value != value.strip()) or (any(c in value for c in '\\/:*?"<>|')):
        _raiseValidationException(("%r is not a valid filename.") % (_errstr(value)), excMsg, [value])
    return value


def validateFilepath(
    value, blank=False, strip=None, allowRegexes=None, blockRegexes=None, whiteList=None, blackList=None, excMsg=None
):
    # type: (str, bool, Union[None, str, bool], Union[None, Sequence[Union[Pattern, str]]], Union[None, Sequence[Union[Pattern, str, Sequence[Union[Pattern, str]]]]], Optional[str], bool) -> str
    returnNow, value = _prevalidationCheck(value, blank, strip, allowRegexes, blockRegexes, whiteList, blackList, excMsg)
    if returnNow:
        return value

    if (value != value.strip()) or (
        any(c in value for c in '*?"<>|')
    ):  # Same as validateFilename, except we allow \ and / and :
        if ":" in value:
            if value.find(":", 2) != -1 or not value[0].isalpha():
                # For Windows: Colon can only be found at the beginning, e.g. 'C:\', or the first letter is not a letter drive.
                _raiseValidationException(("%r is not a valid file path.") % (_errstr(value)), excMsg, [value])
        _raiseValidationException(("%r is not a valid file path.") % (_errstr(value)), excMsg, [value])
    return value
    raise NotImplementedError()


def validateIP(value, blank=False, strip=None, allowRegexes=None, blockRegexes=None, whiteList=None, blackList=None, excMsg=None):
    # type: (str, bool, Union[None, str, bool], Union[None, Sequence[Union[Pattern, str]]], Union[None, Sequence[Union[Pattern, str, Sequence[Union[Pattern, str]]]]], Optional[str]) -> str

    # Validate parameters.
    _validateGenericParameters(blank=blank, strip=strip, allowRegexes=allowRegexes, blockRegexes=blockRegexes)

    returnNow, value = _prevalidationCheck(value, blank, strip, allowRegexes, blockRegexes, whiteList, blackList, excMsg)
    if returnNow:
        return value

    # Reuse the logic in validateRegex()
    try:
        try:
            # Check if value is an IPv4 address.
            return validateRegex(
                value=value,
                regex=IPV4_REGEX,
                blank=blank,
                strip=strip,
                allowRegexes=allowRegexes,
                blockRegexes=blockRegexes,
            )
        except:
            pass  # Go on to check if it's an IPv6 address.

        # Check if value is an IPv6 address.
        return validateRegex(
            value=value,
            regex=IPV6_REGEX,
            blank=blank,
            strip=strip,
            allowRegexes=allowRegexes,
            blockRegexes=blockRegexes,
        )
    except ValidationException:
        _raiseValidationException(("%r is not a valid IP address.") % (_errstr(value)), excMsg, [value])
    assert False, "The execution reached this point, even though the previous line should have raised an exception."


def validateIPv4(value, blank=False, strip=None, allowRegexes=None, blockRegexes=None, whiteList=None, blackList=None, excMsg=None):
    # type: (str, bool, Union[None, str, bool], Union[None, Sequence[Union[Pattern, str]]], Union[None, Sequence[Union[Pattern, str, Sequence[Union[Pattern, str]]]]], Optional[str]) -> str


    # Validate parameters.
    _validateGenericParameters(blank=blank, strip=strip, allowRegexes=allowRegexes, blockRegexes=blockRegexes)

    returnNow, value = _prevalidationCheck(value, blank, strip, allowRegexes, blockRegexes, whiteList, blackList, excMsg)
    if returnNow:
        return value

    # Reuse the logic in validateRegex()

    try:
        # Check if value is an IPv4 address.
        return validateRegex(
            value=value,
            regex=IPV4_REGEX,
            blank=blank,
            strip=strip,
            allowRegexes=allowRegexes,
            blockRegexes=blockRegexes,
        )
    except ValidationException:
        _raiseValidationException(("%r is not a valid IPv4 address.") % (_errstr(value)), excMsg, [value])
    assert False, "The execution reached this point, even though the previous line should have raised an exception."


def validateIPv6(value, blank=False, strip=None, allowRegexes=None, blockRegexes=None, whiteList=None, blackList=None, excMsg=None):
    # type: (str, bool, Union[None, str, bool], Union[None, Sequence[Union[Pattern, str]]], Union[None, Sequence[Union[Pattern, str, Sequence[Union[Pattern, str]]]]], Optional[str]) -> str

    # Validate parameters.
    _validateGenericParameters(blank=blank, strip=strip, allowRegexes=allowRegexes, blockRegexes=blockRegexes)

    returnNow, value = _prevalidationCheck(value, blank, strip, allowRegexes, blockRegexes, whiteList, blackList, excMsg)
    if returnNow:
        return value

    # Reuse the logic in validateRegex()
    try:
        # Check if value is an IPv6 address.
        return validateRegex(
            value=value,
            regex=IPV6_REGEX,
            blank=blank,
            strip=strip,
            allowRegexes=allowRegexes,
            blockRegexes=blockRegexes,
        )
    except ValidationException:
        _raiseValidationException(("%r is not a valid IPv6 address.") % (_errstr(value)), excMsg, [value])
    assert False, "The execution reached this point, even though the previous line should have raised an exception."


def validateRegex(value, regex, flags=0, blank=False, strip=None, allowRegexes=None, blockRegexes=None, whiteList=None, blackList=None, excMsg=None):
    # type: (str, Union[str, Pattern], int, bool, Union[None, str, bool], Union[None, Sequence[Union[Pattern, str]]], Union[None, Sequence[Union[Pattern, str, Sequence[Union[Pattern, str]]]]], Optional[str]) -> str


    # Validate parameters.
    _validateGenericParameters(blank=blank, strip=strip, allowRegexes=allowRegexes, blockRegexes=blockRegexes)

    returnNow, value = _prevalidationCheck(value, blank, strip, allowRegexes, blockRegexes, whiteList, blackList, excMsg)
    if returnNow:
        return value

    # Search value with regex, whether regex is a str or regex object.
    if isinstance(regex, str):
        # TODO - check flags to see they're valid regex flags.
        mo = re.compile(regex, flags).search(value)
    elif isinstance(regex, REGEX_TYPE):
        mo = regex.search(value)
    else:
        raise PySimpleValidateException("regex must be a str or regex object")

    if mo is not None:
        return mo.group()
    else:
        _raiseValidationException(("%r does not match the specified pattern.") % (_errstr(value)), excMsg, [value])
    assert False, "The execution reached this point, even though the previous line should have raised an exception."


def validateRegexStr(value, blank=False, strip=None, allowRegexes=None, blockRegexes=None, whiteList=None, blackList=None, excMsg=None):
    # type: (str, bool, Union[None, str, bool], Union[None, Sequence[Union[Pattern, str]]], Union[None, Sequence[Union[Pattern, str, Sequence[Union[Pattern, str]]]]], Optional[str]) -> Union[str, Pattern]


    # TODO - I'd be nice to check regexes in other languages, i.e. JS and Perl.
    _validateGenericParameters(blank=blank, strip=strip, allowRegexes=allowRegexes, blockRegexes=blockRegexes)

    returnNow, value = _prevalidationCheck(value, blank, strip, allowRegexes, blockRegexes, whiteList, blackList, excMsg)
    if returnNow:
        return value

    try:
        return re.compile(value)
    except Exception as ex:
        _raiseValidationException(("%r is not a valid regular expression: %s") % (_errstr(value), ex), excMsg, [value], ex)
    assert False, "The execution reached this point, even though the previous line should have raised an exception."


def validateURL(value, blank=False, strip=None, allowRegexes=None, blockRegexes=None, whiteList=None, blackList=None, excMsg=None):
    # type: (str, bool, Union[None, str, bool], Union[None, Sequence[Union[Pattern, str]]], Union[None, Sequence[Union[Pattern, str, Sequence[Union[Pattern, str]]]]], Optional[str]) -> str


    # Reuse the logic in validateRegex()
    try:
        return validateRegex(
            value=value, regex=URL_REGEX, blank=blank, strip=strip, allowRegexes=allowRegexes, blockRegexes=blockRegexes, whiteList=whiteList, blackList=whiteList,
        )
    except ValidationException:
        # 'localhost' is also an acceptable URL:
        if value == "localhost":
            return "localhost"

        _raiseValidationException(("%r is not a valid URL.") % (value, ), excMsg, [value])
    assert False, "The execution reached this point, even though the previous line should have raised an exception."


def validateEmail(value, blank=False, strip=None, allowRegexes=None, blockRegexes=None, whiteList=None, blackList=None, excMsg=None):
    # type: (str, bool, Union[None, str, bool], Union[None, Sequence[Union[Pattern, str]]], Union[None, Sequence[Union[Pattern, str, Sequence[Union[Pattern, str]]]]], Optional[str]) -> str


    # Reuse the logic in validateRegex()
    try:
        return validateRegex(
            value=value,
            regex=EMAIL_REGEX,
            blank=blank,
            strip=strip,
            allowRegexes=allowRegexes,
            blockRegexes=blockRegexes,
            whiteList=whiteList,
            blackList=blackList,
        )
    except ValidationException:
        _raiseValidationException(("%r is not a valid email address.") % (value, ), excMsg, [value])
    assert False, "The execution reached this point, even though the previous line should have raised an exception."


def validateYesNo(
    value,
    blank=False,
    strip=None,
    allowRegexes=None,
    blockRegexes=None,
    yesVal="yes",
    noVal="no",
    caseSensitive=False,
    excMsg=None,
):
    # type: (str, bool, Union[None, str, bool], Union[None, Sequence[Union[Pattern, str]]], Union[None, Sequence[Union[Pattern, str, Sequence[Union[Pattern, str]]]]], str, str, bool, Optional[str]) -> str


    # Validate parameters. TODO - can probably improve this to remove the duplication.
    _validateGenericParameters(blank=blank, strip=strip, allowRegexes=allowRegexes, blockRegexes=blockRegexes)

    returnNow, value = _prevalidationCheck(value, blank, strip, allowRegexes, blockRegexes, excMsg=excMsg)
    if returnNow:
        return value

    yesVal = str(yesVal)
    noVal = str(noVal)
    if len(yesVal) == 0:
        raise PySimpleValidateException("yesVal argument must be a non-empty string.")
    if len(noVal) == 0:
        raise PySimpleValidateException("noVal argument must be a non-empty string.")
    if (yesVal == noVal) or (not caseSensitive and yesVal.upper() == noVal.upper()):
        raise PySimpleValidateException("yesVal and noVal arguments must be different.")
    if (yesVal[0] == noVal[0]) or (not caseSensitive and yesVal[0].upper() == noVal[0].upper()):
        raise PySimpleValidateException("first character of yesVal and noVal arguments must be different")

    returnNow, value = _prevalidationCheck(value, blank, strip, allowRegexes, blockRegexes, excMsg=excMsg)
    if returnNow:
        return value

    if caseSensitive:
        if value in (yesVal, yesVal[0]):
            return yesVal
        elif value in (noVal, noVal[0]):
            return noVal
    else:
        if value.upper() in (yesVal.upper(), yesVal[0].upper()):
            return yesVal
        elif value.upper() in (noVal.upper(), noVal[0].upper()):
            return noVal

    _raiseValidationException(("%r is not a valid %s/%s response.") % (_errstr(value), yesVal, noVal), excMsg, [value, yesVal, noVal])
    assert False, "The execution reached this point, even though the previous line should have raised an exception."


def validateBool(
    value,
    blank=False,
    strip=None,
    allowRegexes=None,
    blockRegexes=None,
    trueVal="True",
    falseVal="False",
    caseSensitive=False,
    excMsg=None,
):
    # type: (str, bool, Union[None, str, bool], Union[None, Sequence[Union[Pattern, str]]], Union[None, Sequence[Union[Pattern, str, Sequence[Union[Pattern, str]]]]], str, str, bool, Optional[str]) -> Union[bool, str]


    # Validate parameters. TODO - can probably improve this to remove the duplication.
    _validateGenericParameters(blank=blank, strip=strip, allowRegexes=allowRegexes, blockRegexes=blockRegexes)

    returnNow, value = _prevalidationCheck(value, blank, strip, allowRegexes, blockRegexes, excMsg=excMsg)
    if returnNow:
        return value

    # Replace the exception messages used in validateYesNo():
    trueVal = str(trueVal)
    falseVal = str(falseVal)
    if len(trueVal) == 0:
        raise PySimpleValidateException("trueVal argument must be a non-empty string.")
    if len(falseVal) == 0:
        raise PySimpleValidateException("falseVal argument must be a non-empty string.")
    if (trueVal == falseVal) or (not caseSensitive and trueVal.upper() == falseVal.upper()):
        raise PySimpleValidateException("trueVal and noVal arguments must be different.")
    if (trueVal[0] == falseVal[0]) or (not caseSensitive and trueVal[0].upper() == falseVal[0].upper()):
        raise PySimpleValidateException("first character of trueVal and noVal arguments must be different")

    try:
        result = validateYesNo(
            value,
            blank=blank,
            strip=strip,
            allowRegexes=allowRegexes,
            blockRegexes=blockRegexes,
            yesVal=trueVal,
            noVal=falseVal,
            caseSensitive=caseSensitive,
            excMsg=excMsg,
        )
    except ValidationException:
        _raiseValidationException(("%r is not a valid %s/%s response.") % (_errstr(value), trueVal, falseVal), excMsg, [value, trueVal, falseVal])

    # Return a bool value instead of a string.
    if result == trueVal:
        return True
    elif result == falseVal:
        return False
    else:
        assert (
            False
        ), "inner validateYesNo() call returned something that was not yesVal or noVal. This should never happen."


def validateUSState(
    value, blank=False, strip=None, allowRegexes=None, blockRegexes=None, whiteList=None, blackList=None, excMsg=None, returnStateName=False
):
    # type: (str, bool, Union[None, str, bool], Union[None, Sequence[Union[Pattern, str]]], Union[None, Sequence[Union[Pattern, str, Sequence[Union[Pattern, str]]]]], Optional[str], bool) -> str


    # TODO - note that this is USA-centric. I should work on trying to make this more international.

    # Validate parameters.
    _validateGenericParameters(blank=blank, strip=strip, allowRegexes=allowRegexes, blockRegexes=blockRegexes)

    returnNow, value = _prevalidationCheck(value, blank, strip, allowRegexes, blockRegexes, whiteList, blackList, excMsg)
    if returnNow:
        return value

    if value.upper() in USA_STATES_UPPER.keys():  # check if value is a state abbreviation
        if returnStateName:
            return USA_STATES[value.upper()]  # Return full state name.
        else:
            return value.upper()  # Return abbreviation.
    elif value.title() in USA_STATES.values():  # check if value is a state name
        if returnStateName:
            return value.title()  # Return full state name.
        else:
            return USA_STATES_REVERSED[value.title()]  # Return abbreviation.

    _raiseValidationException(("%r is not a state.") % (_errstr(value)), excMsg, [value])
    assert False, "The execution reached this point, even though the previous line should have raised an exception."


def validateName():
    raise NotImplementedError()


def validateAddress():
    raise NotImplementedError()


def validatePhone():
    raise NotImplementedError()


def validateMonth(
    value, blank=False, strip=None, allowRegexes=None, blockRegexes=None, whiteList=None, blackList=None, monthNames=ENGLISH_MONTHS, excMsg=None
):
    # type: (str, bool, Union[None, str, bool], Union[None, Sequence[Union[Pattern, str]]], Union[None, Sequence[Union[Pattern, str, Sequence[Union[Pattern, str]]]]], Dict[str, str], Optional[str]) -> str


    # returns full month name, e.g. 'January'

    # Validate parameters.
    _validateGenericParameters(blank=blank, strip=strip, allowRegexes=allowRegexes, blockRegexes=blockRegexes)

    returnNow, value = _prevalidationCheck(value, blank, strip, allowRegexes, blockRegexes, whiteList, blackList, excMsg)
    if returnNow:
        return value

    try:
        if (monthNames == ENGLISH_MONTHS) and (
            1 <= int(value) <= 12
        ):  # This check here only applies to months, not when validateDayOfWeek() calls this function.
            return ENGLISH_MONTH_NAMES[int(value) - 1]
    except:
        pass  # continue if the user didn't enter a number 1 to 12.

    # Both month names and month abbreviations will be at least 3 characters.
    if len(value) < 3:
        _raiseValidationException(("%r is not a month.") % (_errstr(value)), excMsg, [value])

    if value[:3].upper() in monthNames.keys():  # check if value is a month abbreviation
        return monthNames[value[:3].upper()]  # It turns out that titlecase is good for all the month.
    elif value.upper() in monthNames.values():  # check if value is a month name
        return value.title()

    _raiseValidationException(("%r is not a month.") % (_errstr(value)), excMsg, [value])
    assert False, "The execution reached this point, even though the previous line should have raised an exception."


def validateDayOfWeek(
    value, blank=False, strip=None, allowRegexes=None, blockRegexes=None, whiteList=None, blackList=None, excMsg=None
):
    # type: (str, bool, Union[None, str, bool], Union[None, Sequence[Union[Pattern, str]]], Union[None, Sequence[Union[Pattern, str, Sequence[Union[Pattern, str]]]]], Dict[str, str], Optional[str]) -> str


    # TODO - reuse validateChoice for this function

    # returns full day of the week str, e.g. 'Sunday'

    # Reuses validateMonth.
    try:
        return validateMonth(
            value,
            blank=blank,
            strip=strip,
            allowRegexes=allowRegexes,
            blockRegexes=blockRegexes,
            whiteList=whiteList,
            blackList=blackList,
            monthNames=ENGLISH_DAYS_OF_WEEK,
        )
    except:
        # Replace the exception message.
        _raiseValidationException(("%r is not a day of the week.") % (_errstr(value)), excMsg, [value])
    assert False, "The execution reached this point, even though the previous line should have raised an exception."


def validateDayOfMonth(value, year, month, blank=False, strip=None, allowRegexes=None, blockRegexes=None, whiteList=None, blackList=None, excMsg=None):
    # type: (str, int, int, bool, Union[None, str, bool], Union[None, Sequence[Union[Pattern, str]]], Union[None, Sequence[Union[Pattern, str, Sequence[Union[Pattern, str]]]]], Optional[str]) -> int

    year = int(year)
    month = int(month)
    try:
        daysInMonth = calendar.monthrange(year, month)[1]
    except:
        raise PySimpleValidateException("invalid arguments for year and/or month")

    try:
        return int(
            validateInt(
                value,
                blank=blank,
                strip=strip,
                allowRegexes=allowRegexes,
                blockRegexes=blockRegexes,
                whiteList=whiteList,
                blackList=blackList,
                min=1,
                max=daysInMonth,
            )
        )
    except:
        # Replace the exception message.
        _raiseValidationException(
            ("%r is not a day in the month of %s %s.") % (_errstr(value), ENGLISH_MONTH_NAMES[month - 1], year), excMsg, [value, ENGLISH_MONTH_NAMES[month - 1], year]
        )
    assert False, "The execution reached this point, even though the previous line should have raised an exception."

    def parameters():
        pass  # This "function" only exists so you can call `help()`


def _checkLimitAndTimeout(startTime, timeout, tries, limit):
    # type: (float, Optional[float], int, Optional[int]) -> Union[None, TimeoutException, RetryLimitException]

    # NOTE: We return exceptions instead of raising them so the caller
    # can still display the original validation exception message.
    if timeout is not None and startTime + timeout < time.time():
        return TimeoutException()

    if limit is not None and tries >= limit:
        return RetryLimitException()

    return None  # Returns None if there was neither a timeout or limit exceeded.


def _genericInput(
        prompt="",
        default=None,
        timeout=None,
        limit=None,
        applyFunc=None,
        validationFunc=None,
        postValidateApplyFunc=None,
        passwordMask=None,
):
    # type: (str, Any, Optional[float], Optional[int], Optional[Callable], Optional[Callable], Optional[Callable], Optional[str]) -> Any

    # NOTE: _genericInput() can return any type of value. Any type casting must be done by the caller.
    # Validate the parameters.
    if not isinstance(prompt, str):
        raise PyInputPlusException("prompt argument must be a str")
    if not isinstance(timeout, (int, float, type(None))):
        raise PyInputPlusException("timeout argument must be an int or float")
    if not isinstance(limit, (int, type(None))):
        raise PyInputPlusException("limit argument must be an int")
    if not callable(validationFunc):
        raise PyInputPlusException("validationFunc argument must be a function")
    if not (callable(applyFunc) or applyFunc is None):
        raise PyInputPlusException("applyFunc argument must be a function or None")
    if not (callable(postValidateApplyFunc) or postValidateApplyFunc is None):
        raise PyInputPlusException("postValidateApplyFunc argument must be a function or None")
    if passwordMask is not None and (not isinstance(passwordMask, str) or len(passwordMask) > 1):
        raise PyInputPlusException("passwordMask argument must be None or a single-character string.")

    startTime = time.time()
    tries = 0

    while True:
        # Get the user input.
        builtins.print(prompt, end="")
        if passwordMask is None:
            userInput = builtins.input()
        else:
            userInput = getpass(prompt="", mask=passwordMask)
        tries += 1

        # Transform the user input with the applyFunc function.
        if applyFunc is not None:
            userInput = applyFunc(userInput)

        # Run the validation function.
        try:
            possibleNewUserInput = validationFunc(
                userInput
            )  # If validation fails, this function will raise an exception. Returns an updated value to use as user input (e.g. stripped of whitespace, etc.)
            if possibleNewUserInput is not None:
                userInput = possibleNewUserInput
        except Exception as exc:
            # Check if they have timed out or reach the retry limit. (If so,
            # the TimeoutException/RetryLimitException overrides the validation
            # exception that was just raised.)
            limitOrTimeoutException = _checkLimitAndTimeout(
                startTime=startTime, timeout=timeout, tries=tries, limit=limit
            )

            print(exc)  # Display the message of the validation exception.

            if isinstance(limitOrTimeoutException, Exception):
                if default is not None:
                    # If there was a timeout/limit exceeded, return the default value if there is one.
                    return default
                else:
                    # If there is no default, then raise the timeout/limit exception.
                    raise limitOrTimeoutException
            else:
                # If there was no timeout/limit exceeded, let the user enter input again.
                continue

        # The previous call to _checkLimitAndTimeout() only happens when the
        # user enteres invalid input. Now we should check for a timeout even if
        # the last input was valid.
        if timeout is not None and startTime + timeout < time.time():
            # It doesn't matter that the user entered valid input, they've
            # exceeded the timeout so we either return the default or raise
            # TimeoutException.
            if default is not None:
                return default
            else:
                raise TimeoutException()

        if postValidateApplyFunc is not None:
            return postValidateApplyFunc(userInput)
        else:
            return userInput


def inputStr(
        prompt="",
        default=None,
        blank=False,
        timeout=None,
        limit=None,
        strip=None,
        allowRegexes=None,
        blockRegexes=None,
        whiteList=None,
        blackList=None,
        applyFunc=None,
        postValidateApplyFunc=None,
        errorMessage=None
):
    # type: (str, Any, bool, Optional[float], Optional[int], Union[None, str, bool], Union[None, Sequence[Union[Pattern, str]]], Union[None, Sequence[Union[Pattern, str, Sequence[Union[Pattern, str]]]]], Optional[Callable], Optional[Callable]) -> Any

    # Validate the arguments passed to validateNum().
    _validateGenericParameters(blank, strip, allowRegexes, blockRegexes)

    validationFunc = lambda value: _prevalidationCheck(
        value, blank=blank, strip=strip, allowRegexes=allowRegexes, blockRegexes=blockRegexes, whiteList=whiteList,
        blackList=blackList, excMsg=errorMessage,
    )[1]

    return _genericInput(
        prompt=prompt,
        default=default,
        timeout=timeout,
        limit=limit,
        applyFunc=applyFunc,
        postValidateApplyFunc=postValidateApplyFunc,
        validationFunc=validationFunc,
    )


def inputCustom(
        customValidationFunc,
        prompt="",
        default=None,
        blank=False,
        timeout=None,
        limit=None,
        strip=None,
        allowRegexes=None,
        blockRegexes=None,
        whiteList=None,
        blackList=None,
        applyFunc=None,
        postValidateApplyFunc=None,
):
    # type: (Callable, str, Any, bool, Optional[float], Optional[int], Union[None, str, bool], Union[None, Sequence[Union[Pattern, str]]], Union[None, Sequence[Union[Pattern, str, Sequence[Union[Pattern, str]]]]], Optional[Callable], Optional[Callable]) -> Any

    # Validate the arguments passed to pysv.validateNum().
    _validateGenericParameters(blank, strip, allowRegexes, blockRegexes)

    # Our validationFunc argument must also call pysv._prevalidationCheck()
    def validationFunc(value):
        value = _prevalidationCheck(
            value, blank=blank, strip=strip, allowRegexes=allowRegexes, blockRegexes=None, whiteList=whiteList,
            blackList=blackList, excMsg=None,
        )[1]
        return customValidationFunc(value)

    return _genericInput(
        prompt=prompt,
        default=default,
        timeout=timeout,
        limit=limit,
        applyFunc=applyFunc,
        postValidateApplyFunc=postValidateApplyFunc,
        validationFunc=validationFunc,
    )


def inputNum(
        prompt="",
        default=None,
        blank=False,
        timeout=None,
        limit=None,
        strip=None,
        allowRegexes=None,
        blockRegexes=None,
        whiteList=None,
        blackList=None,
        applyFunc=None,
        postValidateApplyFunc=None,
        min=None,
        max=None,
        greaterThan=None,
        lessThan=None,
        errorMessage=None,
):
    # type: (str, Any, bool, Optional[float], Optional[int], Union[None, str, bool], Union[None, Sequence[Union[Pattern, str]]], Union[None, Sequence[Union[Pattern, str, Sequence[Union[Pattern, str]]]]], Optional[Callable], Optional[Callable], Optional[float], Optional[float], Optional[float], Optional[float]) -> Any

    # Validate the arguments passed to validateNum().

    _validateParamsFor_validateNum(min=min, max=max, lessThan=lessThan, greaterThan=greaterThan)

    validationFunc = lambda value: validateNum(
        value,
        blank=blank,
        strip=strip,
        allowRegexes=allowRegexes,
        blockRegexes=blockRegexes,
        whiteList=whiteList,
        blackList=blackList,
        min=min,
        max=max,
        lessThan=lessThan,
        greaterThan=greaterThan,
        _numType="num",
        excMsg=errorMessage
    )

    return _genericInput(
        prompt=prompt,
        default=default,
        timeout=timeout,
        limit=limit,
        applyFunc=applyFunc,
        postValidateApplyFunc=postValidateApplyFunc,
        validationFunc=validationFunc,
    )


def inputInt(
        prompt="",
        default=None,
        blank=False,
        timeout=None,
        limit=None,
        strip=None,
        allowRegexes=None,
        blockRegexes=None,
        whiteList=None,
        blackList=None,
        applyFunc=None,
        postValidateApplyFunc=None,
        min=None,
        max=None,
        lessThan=None,
        greaterThan=None,
        errorMessage=None,
):
    # type: (str, Any, bool, Optional[float], Optional[int], Union[None, str, bool], Union[None, Sequence[Union[Pattern, str]]], Union[None, Sequence[Union[Pattern, str, Sequence[Union[Pattern, str]]]]], Optional[Callable], Optional[Callable], Optional[float], Optional[float], Optional[float], Optional[float]) -> Any
    # Validate the arguments passed to validateNum().
    _validateParamsFor_validateNum(min=min, max=max, lessThan=lessThan, greaterThan=greaterThan)

    validationFunc = lambda value: validateNum(
        value,
        blank=blank,
        strip=strip,
        allowRegexes=allowRegexes,
        blockRegexes=blockRegexes,
        whiteList=whiteList,
        blackList=blackList,
        min=min,
        max=max,
        lessThan=lessThan,
        greaterThan=greaterThan,
        _numType="int",
        excMsg=errorMessage
    )

    result = _genericInput(
        prompt=prompt,
        default=default,
        timeout=timeout,
        limit=limit,
        applyFunc=applyFunc,
        validationFunc=validationFunc,
    )

    try:
        result = int(float(result))
    except ValueError:
        # In case _genericInput() returned the default value or an allowlist value, return that as is instead.
        pass

    if postValidateApplyFunc is None:
        return result
    else:
        return postValidateApplyFunc(result)


def inputFloat(
        prompt="",
        default=None,
        blank=False,
        timeout=None,
        limit=None,
        strip=None,
        allowRegexes=None,
        blockRegexes=None,
        whiteList=None,
        blackList=None,
        applyFunc=None,
        postValidateApplyFunc=None,
        min=None,
        max=None,
        lessThan=None,
        greaterThan=None,
        errorMessage=None,
):
    # type: (str, Any, bool, Optional[float], Optional[int], Union[None, str, bool], Union[None, Sequence[Union[Pattern, str]]], Union[None, Sequence[Union[Pattern, str, Sequence[Union[Pattern, str]]]]], Optional[Callable], Optional[Callable], Optional[float], Optional[float], Optional[float], Optional[float]) -> Any
    # Validate the arguments passed to validateNum().
    _validateParamsFor_validateNum(min=min, max=max, lessThan=lessThan, greaterThan=greaterThan)

    validationFunc = lambda value: validateNum(
        value,
        blank=blank,
        strip=strip,
        allowRegexes=allowRegexes,
        blockRegexes=blockRegexes,
        whiteList=whiteList,
        blackList=blackList,
        min=min,
        max=max,
        lessThan=lessThan,
        greaterThan=greaterThan,
        _numType="float",
        excMsg=errorMessage
    )

    result = _genericInput(
        prompt=prompt,
        default=default,
        timeout=timeout,
        limit=limit,
        applyFunc=applyFunc,
        validationFunc=validationFunc,
    )

    try:
        result = float(result)
    except ValueError:
        # In case _genericInput() returned the default value or an allowlist value, return that as is instead.
        pass

    if postValidateApplyFunc is None:
        return result
    else:
        return postValidateApplyFunc(result)


def inputChoice(
        choices,
        prompt="_default",
        default=None,
        blank=False,
        timeout=None,
        limit=None,
        strip=None,
        allowRegexes=None,
        blockRegexes=None,
        whiteList=None,
        blackList=None,
        applyFunc=None,
        postValidateApplyFunc=None,
        caseSensitive=False,
        errorMessage=None,
):
    # type: (Sequence[str], str, Any, bool, Optional[float], Optional[int], Union[None, str, bool], Union[None, Sequence[Union[Pattern, str]]], Union[None, Sequence[Union[Pattern, str, Sequence[Union[Pattern, str]]]]], Optional[Callable], Optional[Callable], bool) -> Any

    # Validate the arguments passed to validateChoice().
    _validateParamsFor_validateChoice(
        choices,
        blank=blank,
        strip=strip,
        allowRegexes=allowRegexes,
        blockRegexes=blockRegexes,
        whiteList=whiteList,
        blackList=blackList,
        numbered=False,
        lettered=False,
        caseSensitive=caseSensitive,
    )

    validationFunc = lambda value: validateChoice(
        value,
        choices=choices,
        blank=blank,
        strip=strip,
        allowRegexes=allowRegexes,
        blockRegexes=blockRegexes,
        whiteList=whiteList,
        blackList=blackList,
        numbered=False,
        lettered=False,
        caseSensitive=False,
        excMsg=errorMessage
    )

    if prompt == "_default":
        prompt = "Please select one of: %s\n" % (", ".join(choices))

    return _genericInput(
        prompt=prompt,
        default=default,
        timeout=timeout,
        limit=limit,
        applyFunc=applyFunc,
        postValidateApplyFunc=postValidateApplyFunc,
        validationFunc=validationFunc,
    )


def inputMenu(
        choices,
        prompt="_default",
        default=None,
        blank=False,
        timeout=None,
        limit=None,
        strip=None,
        allowRegexes=None,
        blockRegexes=None,
        whiteList=None,
        blackList=None,
        applyFunc=None,
        postValidateApplyFunc=None,
        numbered=False,
        lettered=False,
        caseSensitive=False,
        errorMessage=None,
):
    # type: (Sequence[str], str, Any, bool, Optional[float], Optional[int], Union[None, str, bool], Union[None, Sequence[Union[Pattern, str]]], Union[None, Sequence[Union[Pattern, str, Sequence[Union[Pattern, str]]]]], Optional[Callable], Optional[Callable], bool, bool, bool) -> Any

    # Validate the arguments passed to validateChoice().
    _validateParamsFor_validateChoice(
        choices,
        blank=blank,
        strip=strip,
        blockRegexes=None,
        numbered=numbered,
        lettered=lettered,
        caseSensitive=caseSensitive,
    )

    validationFunc = lambda value: validateChoice(
        value,
        choices=choices,
        blank=blank,
        strip=strip,
        allowRegexes=allowRegexes,
        blockRegexes=None,
        whiteList=whiteList,
        blackList=blackList,
        numbered=numbered,
        lettered=lettered,
        caseSensitive=caseSensitive,
        excMsg=errorMessage
    )

    if prompt == "_default":
        prompt = "Please select one of the following:\n"

    if numbered:
        prompt += "\n".join([str(i + 1) + ". " + choices[i] for i in range(len(choices))])
    elif lettered:
        prompt += "\n".join([chr(65 + i) + ". " + choices[i] for i in range(len(choices))])
    else:
        prompt += "\n".join(["* " + choice for choice in choices])
    prompt += "\n"

    result = _genericInput(
        prompt=prompt,
        default=default,
        timeout=timeout,
        limit=limit,
        applyFunc=applyFunc,
        validationFunc=validationFunc,
    )

    # Since ``result`` could be a number or letter of the option selected, we
    # need to find the string in ``choices`` to return. Call ``validateChoice()``
    # again to get it.
    result = validateChoice(
        result,
        choices,
        blank=blank,
        strip=strip,
        allowRegexes=allowRegexes,
        blockRegexes=None,
        whiteList=whiteList,
        blackList=blackList,
        numbered=numbered,
        lettered=lettered,
        caseSensitive=caseSensitive,
    )
    if postValidateApplyFunc is None:
        return result
    else:
        return postValidateApplyFunc(result)


def inputDate(
        prompt="",
        formats=None,
        default=None,
        blank=False,
        timeout=None,
        limit=None,
        strip=None,
        allowRegexes=None,
        blockRegexes=None,
        whiteList=None,
        blackList=None,
        applyFunc=None,
        postValidateApplyFunc=None,
        errorMessage=None,
):
    # type: (str, Union[str, Sequence[str]], Any, bool, Optional[float], Optional[int], Union[None, str, bool], Union[None, Sequence[Union[Pattern, str]]], Union[None, Sequence[Union[Pattern, str, Sequence[Union[Pattern, str]]]]], Optional[Callable], Optional[Callable]) -> Any

    if formats is None:
        formats = ("%m/%d/%Y", "%m/%d/%y", "%Y/%m/%d", "%y/%m/%d", "%x")

    validationFunc = lambda value: validateDate(
        value, formats=formats, blank=blank, strip=strip, allowRegexes=allowRegexes, blockRegexes=None,
        whiteList=whiteList, blackList=blackList, excMsg=errorMessage
    )

    return _genericInput(
        prompt=prompt,
        default=default,
        timeout=timeout,
        limit=limit,
        applyFunc=applyFunc,
        postValidateApplyFunc=postValidateApplyFunc,
        validationFunc=validationFunc,
    )


def inputDatetime(
        prompt="",
        formats=(
                "%m/%d/%Y %H:%M:%S",
                "%m/%d/%y %H:%M:%S",
                "%Y/%m/%d %H:%M:%S",
                "%y/%m/%d %H:%M:%S",
                "%x %H:%M:%S",
                "%m/%d/%Y %H:%M",
                "%m/%d/%y %H:%M",
                "%Y/%m/%d %H:%M",
                "%y/%m/%d %H:%M",
                "%x %H:%M",
                "%m/%d/%Y %H:%M:%S",
                "%m/%d/%y %H:%M:%S",
                "%Y/%m/%d %H:%M:%S",
                "%y/%m/%d %H:%M:%S",
                "%x %H:%M:%S",
        ),
        default=None,
        blank=False,
        timeout=None,
        limit=None,
        strip=None,
        allowRegexes=None,
        blockRegexes=None,
        whiteList=None,
        blackList=None,
        applyFunc=None,
        postValidateApplyFunc=None,
        errorMessage=None,
):
    validationFunc = lambda value: validateDatetime(
        value, formats=formats, blank=blank, strip=strip, allowRegexes=allowRegexes, blockRegexes=blockRegexes,
        excMsg=errorMessage
    )

    return _genericInput(
        prompt=prompt,
        default=default,
        timeout=timeout,
        limit=limit,
        applyFunc=applyFunc,
        postValidateApplyFunc=postValidateApplyFunc,
        validationFunc=validationFunc,
    )


def inputTime(
        prompt="",
        formats=("%H:%M:%S", "%H:%M", "%X"),
        default=None,
        blank=False,
        timeout=None,
        limit=None,
        strip=None,
        allowRegexes=None,
        blockRegexes=None,
        whiteList=None,
        blackList=None,
        applyFunc=None,
        postValidateApplyFunc=None,
        errorMessage=None,
):
    validationFunc = lambda value: validateTime(
        value, formats=formats, blank=blank, strip=strip, allowRegexes=allowRegexes, blockRegexes=blockRegexes,
        excMsg=errorMessage
    )

    return _genericInput(
        prompt=prompt,
        default=default,
        timeout=timeout,
        limit=limit,
        applyFunc=applyFunc,
        postValidateApplyFunc=postValidateApplyFunc,
        validationFunc=validationFunc,
    )


def inputUSState(
        prompt="",
        default=None,
        blank=False,
        timeout=None,
        limit=None,
        strip=None,
        allowRegexes=None,
        blockRegexes=None,
        whiteList=None,
        blackList=None,
        applyFunc=None,
        postValidateApplyFunc=None,
        returnStateName=False,
        errorMessage=None,
):
    validationFunc = lambda value: validateUSState(
        value,
        blank=blank,
        strip=strip,
        allowRegexes=allowRegexes,
        blockRegexes=None,
        whiteList=whiteList,
        blackList=blackList,
        returnStateName=returnStateName,
        excMsg=errorMessage
    )

    return _genericInput(
        prompt=prompt,
        default=default,
        timeout=timeout,
        limit=limit,
        applyFunc=applyFunc,
        postValidateApplyFunc=postValidateApplyFunc,
        validationFunc=validationFunc,
    )


def inputMonth(
        prompt="",
        default=None,
        blank=False,
        timeout=None,
        limit=None,
        strip=None,
        allowRegexes=None,
        blockRegexes=None,
        whiteList=None,
        blackList=None,
        applyFunc=None,
        postValidateApplyFunc=None,
        errorMessage=None,
):
    # TODO add returnNumber and returnAbbreviation parameters.

    validationFunc = lambda value: validateMonth(
        value, blank=blank, strip=strip, allowRegexes=allowRegexes, blockRegexes=blockRegexes, whiteList=whiteList,
        blackList=blackList
    )

    return _genericInput(
        prompt=prompt,
        default=default,
        timeout=timeout,
        limit=limit,
        applyFunc=applyFunc,
        postValidateApplyFunc=postValidateApplyFunc,
        validationFunc=validationFunc,
    )


def inputDayOfWeek(
        prompt="",
        default=None,
        blank=False,
        timeout=None,
        limit=None,
        strip=None,
        allowRegexes=None,
        blockRegexes=None,
        whiteList=None,
        blackList=None,
        applyFunc=None,
        postValidateApplyFunc=None,
        errorMessage=None,
):
    # TODO - add returnNumber and return abbreivation parameters.

    validationFunc = lambda value: validateDayOfWeek(
        value, blank=blank, strip=strip, allowRegexes=allowRegexes, blockRegexes=blockRegexes, whiteList=whiteList,
        blackList=blackList
    )

    return _genericInput(
        prompt=prompt,
        default=default,
        timeout=timeout,
        limit=limit,
        applyFunc=applyFunc,
        postValidateApplyFunc=postValidateApplyFunc,
        validationFunc=validationFunc,
    )


def inputDayOfMonth(
        year,
        month,
        prompt="",
        default=None,
        blank=False,
        timeout=None,
        limit=None,
        strip=None,
        allowRegexes=None,
        blockRegexes=None,
        whiteList=None,
        blackList=None,
        applyFunc=None,
        postValidateApplyFunc=None,
        errorMessage=None,
):
    validationFunc = lambda value: validateDayOfMonth(
        value, year, month, blank=blank, strip=strip, allowRegexes=allowRegexes, blockRegexes=blockRegexes,
        whiteList=whiteList, blackList=blackList
    )

    return _genericInput(
        prompt=prompt,
        default=default,
        timeout=timeout,
        limit=limit,
        applyFunc=applyFunc,
        postValidateApplyFunc=postValidateApplyFunc,
        validationFunc=validationFunc,
    )


def inputIP(
        prompt="",
        default=None,
        blank=False,
        timeout=None,
        limit=None,
        strip=None,
        allowRegexes=None,
        blockRegexes=None,
        whiteList=None,
        blackList=None,
        applyFunc=None,
        postValidateApplyFunc=None,
):
    validationFunc = lambda value: validateIP(
        value, blank=blank, strip=strip, allowRegexes=allowRegexes, blockRegexes=blockRegexes, whiteList=whiteList,
        blackList=blackList
    )

    return _genericInput(
        prompt=prompt,
        default=default,
        timeout=timeout,
        limit=limit,
        applyFunc=applyFunc,
        postValidateApplyFunc=postValidateApplyFunc,
        validationFunc=validationFunc,
    )


def inputRegex(
        regex,
        flags=0,
        prompt="",
        default=None,
        blank=False,
        timeout=None,
        limit=None,
        strip=None,
        allowRegexes=None,
        blockRegexes=None,
        whiteList=None,
        blackList=None,
        applyFunc=None,
        postValidateApplyFunc=None,
):
    # type: (Union[str, Pattern], int, str, Any, bool, Optional[float], Optional[int], Union[None, str, bool], Union[None, Sequence[Union[Pattern, str]]], Union[None, Sequence[Union[Pattern, str, Sequence[Union[Pattern, str]]]]], Optional[Callable], Optional[Callable]) -> Any

    validationFunc = lambda value: validateRegex(
        value, regex=regex, flags=flags, blank=blank, strip=strip, allowRegexes=allowRegexes, blockRegexes=blockRegexes,
        whiteList=whiteList, blackList=blackList
    )

    return _genericInput(
        prompt=prompt,
        default=default,
        timeout=timeout,
        limit=limit,
        applyFunc=applyFunc,
        postValidateApplyFunc=postValidateApplyFunc,
        validationFunc=validationFunc,
    )


def inputRegexStr(
        prompt="",
        default=None,
        blank=False,
        timeout=None,
        limit=None,
        strip=None,
        allowRegexes=None,
        blockRegexes=None,
        whiteList=None,
        blackList=None,
        applyFunc=None,
        postValidateApplyFunc=None,
):
    # type: (str, Any, bool, Optional[float], Optional[int], Union[None, str, bool], Union[None, Sequence[Union[Pattern, str]]], Union[None, Sequence[Union[Pattern, str, Sequence[Union[Pattern, str]]]]], Optional[Callable], Optional[Callable]) -> Any

    validationFunc = lambda value: validateRegexStr(
        value, blank=blank, strip=strip, allowRegexes=allowRegexes, whiteList=whiteList, blackList=blackList
    )

    return _genericInput(
        prompt=prompt,
        default=default,
        timeout=timeout,
        limit=limit,
        applyFunc=applyFunc,
        postValidateApplyFunc=postValidateApplyFunc,
        validationFunc=validationFunc,
    )


def inputURL(
        prompt="",
        default=None,
        blank=False,
        timeout=None,
        limit=None,
        strip=None,
        allowRegexes=None,
        blockRegexes=None,
        whiteList=None,
        blackList=None,
        applyFunc=None,
        postValidateApplyFunc=None,
):
    # type: (str, Any, bool, Optional[float], Optional[int], Union[None, str, bool], Union[None, Sequence[Union[Pattern, str]]], Union[None, Sequence[Union[Pattern, str, Sequence[Union[Pattern, str]]]]], Optional[Callable], Optional[Callable]) -> Any

    validationFunc = lambda value: validateURL(
        value, blank=blank, strip=strip, allowRegexes=allowRegexes, blockRegexes=blockRegexes, whiteList=whiteList,
        blackList=blackList
    )

    return _genericInput(
        prompt=prompt,
        default=default,
        timeout=timeout,
        limit=limit,
        applyFunc=applyFunc,
        postValidateApplyFunc=postValidateApplyFunc,
        validationFunc=validationFunc,
    )


def inputYesNo(
        prompt="",
        yesVal=None,
        noVal=None,
        caseSensitive=False,
        default=None,
        blank=False,
        timeout=None,
        limit=None,
        strip=None,
        allowRegexes=None,
        blockRegexes=None,
        applyFunc=None,
        postValidateApplyFunc=None,
):
    # type: (str, str, str, bool, Any, bool, Optional[float], Optional[int], Union[None, str, bool], Union[None, Sequence[Union[Pattern, str]]], Union[None, Sequence[Union[Pattern, str, Sequence[Union[Pattern, str]]]]], Optional[Callable], Optional[Callable]) -> Any

    if yesVal is None:
        yesVal = "yes"  # Use the local language "yes" word.
    if noVal is None:
        noVal = "no"  # Use the local language "no" word.

    validationFunc = lambda value: validateYesNo(
        value,
        yesVal=yesVal,
        noVal=noVal,
        caseSensitive=caseSensitive,
        blank=blank,
        strip=strip,
        allowRegexes=allowRegexes,
        blockRegexes=None,
    )

    result = _genericInput(
        prompt=prompt,
        default=default,
        timeout=timeout,
        limit=limit,
        applyFunc=applyFunc,
        validationFunc=validationFunc,
    )

    # If validation passes, return the value that validateYesNo() returned rather than necessarily what the user typed in.
    result = validateYesNo(
        result,
        yesVal=yesVal,
        noVal=noVal,
        caseSensitive=caseSensitive,
        blank=blank,
        strip=strip,
        allowRegexes=allowRegexes,
        blockRegexes=blockRegexes,
    )

    if postValidateApplyFunc is None:
        return result
    else:
        return postValidateApplyFunc(result)


def inputBool(
        prompt="",
        trueVal=None,
        falseVal=None,
        caseSensitive=False,
        default=None,
        blank=False,
        timeout=None,
        limit=None,
        strip=None,
        allowRegexes=None,
        blockRegexes=None,
        applyFunc=None,
        postValidateApplyFunc=None,
):
    # type: (str, str, str, bool, Any, bool, Optional[float], Optional[int], Union[None, str, bool], Union[None, Sequence[Union[Pattern, str]]], Union[None, Sequence[Union[Pattern, str, Sequence[Union[Pattern, str]]]]], Optional[Callable], Optional[Callable]) -> Any

    if trueVal is None:
        trueVal = "True"  # Use the local language "True" word.
    if falseVal is None:
        falseVal = "False"  # Use the local language "False" word.

    validationFunc = lambda value: validateYesNo(
        value,
        yesVal=trueVal,
        noVal=falseVal,
        caseSensitive=caseSensitive,
        blank=blank,
        strip=strip,
        allowRegexes=allowRegexes,
        blockRegexes=blockRegexes,
    )

    result = _genericInput(
        prompt=prompt,
        default=default,
        timeout=timeout,
        limit=limit,
        applyFunc=applyFunc,
        validationFunc=validationFunc,
    )

    # If the user entered a response that is compatible with trueVal or falseVal exactly, get those particular exact strings.
    result = validateBool(
        result,
        caseSensitive=caseSensitive,
        blank=blank,
        strip=strip,
        allowRegexes=allowRegexes,
        blockRegexes=blockRegexes,
    )

    if postValidateApplyFunc is None:
        return result
    else:
        return postValidateApplyFunc(result)


def inputZip(
        prompt="",
        default=None,
        blank=False,
        timeout=None,
        limit=None,
        strip=None,
        allowRegexes=None,
        blockRegexes=None,
        whiteList=None,
        blackList=None,
        applyFunc=None,
        postValidateApplyFunc=None,
):
    # type: (str, Any, bool, Optional[float], Optional[int], Union[None, str, bool], Union[None, Sequence[Union[Pattern, str]]], Union[None, Sequence[Union[Pattern, str, Sequence[Union[Pattern, str]]]]], Optional[Callable], Optional[Callable]) -> Any

    validationFunc = lambda value: validateRegex(
        value,
        regex=r"(\d){3,5}(-\d\d\d\d)?",
        blank=blank,
        strip=strip,
        allowRegexes=allowRegexes,
        blockRegexes=None,
        whiteList=whiteList,
        blackList=blackList,
        excMsg="That is not a valid zip code.",
    )

    return _genericInput(
        prompt=prompt,
        default=default,
        timeout=timeout,
        limit=limit,
        applyFunc=applyFunc,
        postValidateApplyFunc=postValidateApplyFunc,
        validationFunc=validationFunc,
    )


# TODO - Finish the following
def inputName(
        prompt="",
        default=None,
        blank=False,
        timeout=None,
        limit=None,
        strip=None,
        allowRegexes=None,
        blockRegexes=None,
        applyFunc=None,
        postValidateApplyFunc=None,
):
    # type: (str, Any, bool, Optional[float], Optional[int], Union[None, str, bool], Union[None, Sequence[Union[Pattern, str]]], Union[None, Sequence[Union[Pattern, str, Sequence[Union[Pattern, str]]]]], Optional[Callable], Optional[Callable]) -> Any
    raise NotImplementedError()


def inputAddress(
        prompt="",
        default=None,
        blank=False,
        timeout=None,
        limit=None,
        strip=None,
        allowRegexes=None,
        blockRegexes=None,
        applyFunc=None,
        postValidateApplyFunc=None,
):
    # type: (str, Any, bool, Optional[float], Optional[int], Union[None, str, bool], Union[None, Sequence[Union[Pattern, str]]], Union[None, Sequence[Union[Pattern, str, Sequence[Union[Pattern, str]]]]], Optional[Callable], Optional[Callable]) -> Any
    raise NotImplementedError()


def inputPhone(
        prompt="",
        default=None,
        blank=False,
        timeout=None,
        limit=None,
        strip=None,
        allowRegexes=None,
        blockRegexes=None,
        applyFunc=None,
        postValidateApplyFunc=None,
):
    # type: (str, Any, bool, Optional[float], Optional[int], Union[None, str, bool], Union[None, Sequence[Union[Pattern, str]]], Union[None, Sequence[Union[Pattern, str, Sequence[Union[Pattern, str]]]]], Optional[Callable], Optional[Callable]) -> Any
    raise NotImplementedError()


def inputFilename(
        prompt="",
        default=None,
        blank=False,
        timeout=None,
        limit=None,
        strip=None,
        allowRegexes=None,
        blockRegexes=None,
        whiteList=None,
        blackList=None,
        applyFunc=None,
        postValidateApplyFunc=None,
):
    # type: (str, Any, bool, Optional[float], Optional[int], Union[None, str, bool], Union[None, Sequence[Union[Pattern, str]]], Union[None, Sequence[Union[Pattern, str, Sequence[Union[Pattern, str]]]]], Optional[Callable], Optional[Callable]) -> Any

    validationFunc = lambda value: validateFilename(
        value, blank=blank, strip=strip, allowRegexes=allowRegexes, blockRegexes=blockRegexes, whiteList=whiteList,
        blackList=blackList
    )

    return _genericInput(
        prompt=prompt,
        default=default,
        timeout=timeout,
        limit=limit,
        applyFunc=applyFunc,
        postValidateApplyFunc=postValidateApplyFunc,
        validationFunc=validationFunc,
    )


def inputFilepath(
        prompt="",
        default=None,
        blank=False,
        timeout=None,
        limit=None,
        strip=None,
        allowRegexes=None,
        blockRegexes=None,
        whiteList=None,
        blackList=None,
        applyFunc=None,
        postValidateApplyFunc=None,
        mustExist=False,
):
    # type: (str, Any, bool, Optional[float], Optional[int], Union[None, str, bool], Union[None, Sequence[Union[Pattern, str]]], Union[None, Sequence[Union[Pattern, str, Sequence[Union[Pattern, str]]]]], Optional[Callable], Optional[Callable], bool) -> Any

    validationFunc = lambda value: validateFilepath(
        value, blank=blank, strip=strip, allowRegexes=allowRegexes, blockRegexes=None, whiteList=whiteList,
        blackList=blackList, mustExist=mustExist,
    )

    return _genericInput(
        prompt=prompt,
        default=default,
        timeout=timeout,
        limit=limit,
        applyFunc=applyFunc,
        postValidateApplyFunc=postValidateApplyFunc,
        validationFunc=validationFunc,
    )


def inputEmail(
        prompt="",
        default=None,
        blank=False,
        timeout=None,
        limit=None,
        strip=None,
        allowRegexes=None,
        blockRegexes=None,
        whiteList=None,
        blackList=None,
        applyFunc=None,
        postValidateApplyFunc=None,
):
    # type: (str, Any, bool, Optional[float], Optional[int], Union[None, str, bool], Union[None, Sequence[Union[Pattern, str]]], Union[None, Sequence[Union[Pattern, str, Sequence[Union[Pattern, str]]]]], Optional[Callable], Optional[Callable]) -> Any

    validationFunc = lambda value: validateEmail(
        value, blank=blank, strip=strip, allowRegexes=allowRegexes, blockRegexes=blockRegexes, whiteList=whiteList,
        blackList=blackList
    )

    return _genericInput(
        prompt=prompt,
        default=default,
        timeout=timeout,
        limit=limit,
        applyFunc=applyFunc,
        postValidateApplyFunc=postValidateApplyFunc,
        validationFunc=validationFunc,
    )


def inputPassword(
        prompt="",
        mask="*",
        default=None,
        blank=False,
        timeout=None,
        limit=None,
        strip="",
        allowRegexes=None,
        blockRegexes=None,
        whiteList=None,
        blackList=None,
        applyFunc=None,
        postValidateApplyFunc=None,
):
    # type: (str, str, Any, bool, Optional[float], Optional[int], Union[None, str, bool], Union[None, Sequence[Union[Pattern, str]]], Union[None, Sequence[Union[Pattern, str, Sequence[Union[Pattern, str]]]]], Optional[Callable], Optional[Callable]) -> Any

    if mask is not None and len(mask) > 1:
        raise PyInputPlusException("mask argument must be None, '', or a single-character string.")

    _validateGenericParameters(blank, strip, allowRegexes, blockRegexes)

    validationFunc = lambda value: _prevalidationCheck(
        value, blank=blank, strip=strip, allowRegexes=allowRegexes, blockRegexes=None, whiteList=whiteList,
        blackList=blackList, excMsg=None,
    )[1]

    return _genericInput(
        prompt=prompt,
        default=default,
        timeout=timeout,
        limit=limit,
        applyFunc=applyFunc,
        postValidateApplyFunc=postValidateApplyFunc,
        validationFunc=validationFunc,
        passwordMask=mask,
    )