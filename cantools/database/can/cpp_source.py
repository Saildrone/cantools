from __future__ import print_function
from enum import Enum
import time
from decimal import Decimal
import re
from typing import AnyStr

from ...version import __version__
from .c_source import Message, camel_to_snake_case, _strip_blank_lines, _get, _format_decimal, _format_range

CPP_TAB = '    '

HEADER_FMT = '''\
/**
 * The MIT License (MIT)
 *
 * Copyright (c) 2018-2019 Erik Moqvist
 *
 * Permission is hereby granted, free of charge, to any person
 * obtaining a copy of this software and associated documentation
 * files (the "Software"), to deal in the Software without
 * restriction, including without limitation the rights to use, copy,
 * modify, merge, publish, distribute, sublicense, and/or sell copies
 * of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be
 * included in all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
 * EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
 * MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
 * NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
 * BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
 * ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
 * CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 */

/**
 * This file was generated by cantools version {version} {date}.
 */

#ifndef {include_guard}
#define {include_guard}

#include <ostream>

#include "DBC.h"

{declarations}

#endif  // {include_guard}
'''

SOURCE_FMT = '''\
/**
 * The MIT License (MIT)
 *
 * Copyright (c) 2018-2019 Erik Moqvist
 *
 * Permission is hereby granted, free of charge, to any person
 * obtaining a copy of this software and associated documentation
 * files (the "Software"), to deal in the Software without
 * restriction, including without limitation the rights to use, copy,
 * modify, merge, publish, distribute, sublicense, and/or sell copies
 * of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be
 * included in all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
 * EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
 * MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
 * NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
 * BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
 * ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
 * CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 */

/**
 * This file was generated by cantools version {version} {date}.
 */

#include "{header}"

#include <ostream>

{definitions}\
'''

SIGNAL_DECLARATION_FMT = '''\
/**
 * Signal {name}.
 * Message {message_name}
 *
{comment}\
 * Range: {range}
 * Scale: {scale}
 * Offset: {offset}
{additional_comments}\
 */
class {message_name}_{name} : public Signal<{type_name}, {physical_type}> {{
public:
    {choices}
    {message_name}_{name}(const uint8_t* buffer);

    virtual {type_name} Raw() const override;
    virtual bool RawInRange(const {type_name}& value) const override;

    friend std::ostream& operator<<(std::ostream& os, const {message_name}_{name}& signal);
}};
'''

MESSAGE_DECLARATION_FMT = '''\
{signal_constructors}

/**
 * Message {database_message_name}.
 *
{comment}\
 */
class {database_message_name} : public Frame {{
public:
    {database_message_name}();
    {database_message_name}(std::unique_ptr<uint8_t[]>&& other, const size_t size);
    {database_message_name}(uint8_t* buffer, const size_t size);

    friend std::ostream& operator<<(std::ostream& os, const {database_message_name}& frame);

{signal_setters}
{signal_clearers}

{signals}
{static_vars}
}};
'''

MESSAGE_DEFINITION_FMT = '''\
{signal_definitions}
{constructor}
{ostream}
{static_vars}
{signal_setters}
{signal_clearers}
'''

SIGNAL_DEFINITION_FMT = '''\
{message_name}_{name}::{message_name}_{name}(const uint8_t* buffer)
    : Signal({constructor_params})
{{}}

'''

SIGNAL_DEFINITION_RAW_FMT = '''\
{type_name} {message_name}_{name}::Raw() const {{
{contents}
}}

'''

SIGNAL_DEFINITION_RAW_IN_RANGE_FMT = '''\
bool {message_name}_{name}::RawInRange(const {type_name}& value) const {{
    return ({check});
}}
'''

MESSAGE_CONSTRUCTOR_DEFINITION_FMT = '''\
{database_message_name}::{database_message_name}()
    : Frame({id}u, "{database_message_name}", {length}u, {extended}, {cycle_time}u),
{signals}
{{}}

{database_message_name}::{database_message_name}(std::unique_ptr<uint8_t[]>&& other, const size_t size)
    : Frame({id}u, "{database_message_name}", {length}u, {extended}, {cycle_time}u, std::move(other), size),
{signals}
{{}}

{database_message_name}::{database_message_name}(uint8_t* buffer, const size_t size)
    : Frame({id}u, "{database_message_name}", {length}u, {extended}, {cycle_time}u, buffer, size),
{signals}
{{}}
'''


MESSAGE_DEFINITION_OSTREAM_FMT = '''\
std::ostream& operator<<(std::ostream& os, const {database_message_name}& frame) {{
{contents}
    return os;
}}
'''

SIGNAL_DEFINITION_OSTREAM_FMT = '''\
std::ostream& operator<<(std::ostream& os, const {message_name}_{name}& signal) {{
{contents}
    return os;
}}

'''

SIGNAL_DEFINITION_SET_FMT = '''\
bool {database_message_name}::set_{name}(const {physical_type}& value) {{
{contents}
}}
'''

SIGNAL_DEFINITION_CLEAR_FMT = '''\
void {database_message_name}::clear_{name}() {{
{contents}
}}
'''

SIGN_EXTENSION_FMT = '''
    if (({name} & (1{suffix} << {shift})) != 0{suffix}) {{
        {name} |= 0x{mask:x}{suffix};
    }}

'''

def _format_comment_no_tabs(comment):
    if comment:
        return '\n'.join([
            ' * ' + line.rstrip()
            for line in comment.splitlines()
        ]) + '\n *\n'
    else:
        return ''


# TODO this should evaluate outputs to integers/bools as well, just not only std::string or double
# This would require all input DBC files to be modified so that each signal has a corresponding
# SIG_VALTYPE_ attribute in the signal_valtype_list section. See reference, pg 5-6:
# http://read.pudn.com/downloads766/ebook/3041455/DBC_File_Format_Documentation.pdf
# If this is done then can use signal.type_name, with some simple code to determine if the signal is
# a boolean (1 bit size). Then can make use of Signal template param PhysicalDataType accurately, as
# well as hardcode the `std::ostream& operator<<(` with partial template specialization.

def _is_string_signal(signal):
    return signal.unit and (signal.unit.lower() == 'string' or signal.unit.lower() == 'str')

def _signal_physical_type(signal):
    if _is_string_signal(signal):
        return 'std::string'
    return 'double'

def _signal_raw_type(signal):
    if _is_string_signal(signal):
        return 'std::string'
    return signal.type_name

def _generate_signal_declaration(signal, message_name):
    comment = _format_comment_no_tabs(signal.comment)
    range_ = _format_range(signal)
    scale = _get(signal.scale, '-')
    offset = _get(signal.offset, '-')
    additional_comments = ''

    if 'SPN' in signal.dbc.attributes:
        additional_comments += 'SPN: {spn}'.format(spn=signal.dbc.attributes['SPN'].value)

    choices = _generate_choices(signal)
    member = SIGNAL_DECLARATION_FMT.format(name=signal.name,
                                           choices=choices,
                                           message_name=message_name,
                                           comment=comment,
                                           range=range_,
                                           scale=scale,
                                           offset=offset,
                                           additional_comments=_format_comment_no_tabs(additional_comments),
                                           type_name=_signal_raw_type(signal),
                                           physical_type=_signal_physical_type(signal))
    return member


# TODO unused - re-implement if supporting signal multiplexing is desired
def _format_pack_code_mux(message,
                          mux,
                          body_lines_per_index,
                          variable_lines,
                          helper_kinds):
    signal_name, multiplexed_signals = list(mux.items())[0]
    _format_pack_code_signal(message,
                             signal_name,
                             body_lines_per_index,
                             variable_lines,
                             helper_kinds)
    multiplexed_signals_per_id = sorted(list(multiplexed_signals.items()))
    signal_name = camel_to_snake_case(signal_name)

    lines = [
        '',
        'switch (src_p->{}) {{'.format(signal_name)
    ]

    for multiplexer_id, multiplexed_signals in multiplexed_signals_per_id:
        body_lines = _format_pack_code_level(message,
                                             multiplexed_signals,
                                             variable_lines,
                                             helper_kinds)
        lines.append('')
        lines.append('case {}:'.format(multiplexer_id))

        if body_lines:
            lines.extend(body_lines[1:-1])

        lines.append('    break;')

    lines.extend([
        '',
        'default:',
        '    break;',
        '}'])

    return [('    ' + line).rstrip() for line in lines]


def _format_pack_code_string(signal):
    start = signal.start // 8
    length = signal.length // 8

    body_lines = [
        f'{CPP_TAB}clear_{signal.name}();',
        f'{CPP_TAB}int index = {start};',
        f'{CPP_TAB}for (const auto& c : value) {{',
        f'{CPP_TAB}{CPP_TAB}if (index >= {length + start}) {{ break; }}',
        f'{CPP_TAB}{CPP_TAB}buffer_[index] = c;',
        f'{CPP_TAB}{CPP_TAB}index++;',
        f'{CPP_TAB}}}',
        f'{CPP_TAB}return true;'
    ]
    return '\n'.join(body_lines)


def _format_pack_code_signal(message, signal_name):
    signal = message.get_signal_by_name(signal_name)
    if _is_string_signal(signal):
        return _format_pack_code_string(signal)

    fmt = '    uint{}_t {}_encoded = {}.Encode(value);\n'
    pack_content = fmt.format(signal.type_length,
                              signal.snake_name,
                              signal.name)

    body_lines = []
    body_lines.append(f'{CPP_TAB}if (!{signal.name}.RawInRange({signal.snake_name}_encoded)) {{\n{CPP_TAB}{CPP_TAB}return false;\n    }}')
    body_lines.append(f'{CPP_TAB}clear_{signal.name}();\n')

    for index, shift, shift_direction, mask in signal.segments(invert_shift=False):
        fmt = '    buffer_[{}] |= pack_{}_shift<uint{}_t>({}_encoded, {}u, 0x{:02x}u);'
        line = fmt.format(index,
                          shift_direction,
                          signal.type_length,
                          signal.snake_name,
                          shift,
                          mask)
        body_lines.append(line)
    body_lines.append('    return true;')
    return pack_content + '\n'.join(body_lines)


def _format_clear_code_signal(message, signal_name):
    signal = message.get_signal_by_name(signal_name)
    body_lines = []
    for index, _, _, mask in signal.segments(invert_shift=False):
        fmt = '    buffer_[{}] &= ~0x{:02x}u;'
        line = fmt.format(index, mask)
        body_lines.append(line)
    return '\n'.join(body_lines)


def _format_pack_code_level(message,
                            signal_names):
    """Format one pack level in a signal tree."""
    signal_pack = {}

    for signal_name in signal_names:
        pack = ''
        if isinstance(signal_name, dict):
            print('WARNING: Multiplexed signals are not supported')
        else:
            pack = _format_pack_code_signal(message,
                                            signal_name)
        signal_pack[signal_name] = pack
    return signal_pack


def _format_clear_code_level(message,
                            signal_names):
    """Format one clear level in a signal tree."""
    signal_pack = {}

    for signal_name in signal_names:
        pack = ''
        if isinstance(signal_name, dict):
            print('WARNING: Multiplexed signals are not supported')
        else:
            pack = _format_clear_code_signal(message,
                                             signal_name)
        signal_pack[signal_name] = pack
    return signal_pack


def _format_pack_code(message):
    return _format_pack_code_level(message,
                                   message.signal_tree)


def _format_clear_code(message):
    return _format_clear_code_level(message,
                                    message.signal_tree)


# TODO unused - re-implement if supporting signal multiplexing is desired
def _format_unpack_code_mux(message,
                            mux,
                            body_lines_per_index,
                            variable_lines,
                            helper_kinds):
    signal_name, multiplexed_signals = list(mux.items())[0]
    _format_unpack_code_signal(message,
                               signal_name,
                               body_lines_per_index,
                               variable_lines,
                               helper_kinds)
    multiplexed_signals_per_id = sorted(list(multiplexed_signals.items()))
    signal_name = camel_to_snake_case(signal_name)

    lines = [
        'switch (dst_p->{}) {{'.format(signal_name)
    ]

    for multiplexer_id, multiplexed_signals in multiplexed_signals_per_id:
        body_lines = _format_unpack_code_level(message,
                                               multiplexed_signals,
                                               variable_lines,
                                               helper_kinds)
        lines.append('')
        lines.append('case {}:'.format(multiplexer_id))
        lines.extend(_strip_blank_lines(body_lines))
        lines.append('    break;')

    lines.extend([
        '',
        'default:',
        '    break;',
        '}'])

    return [('    ' + line).rstrip() for line in lines]

def _format_unpack_code_string(signal):
    length = signal.length // 8
    start = signal.start // 8
    body_lines = [
        f'{CPP_TAB}char buff[{length + 1}];',
        f'{CPP_TAB}int index = 0;',
        f'{CPP_TAB}while (index < {length}) {{',
        f'{CPP_TAB}{CPP_TAB}char c = buffer_[index + {start}];',
        f'{CPP_TAB}{CPP_TAB}if (c == (char)0xff || c == 0) {{ break; }}',
        f'{CPP_TAB}{CPP_TAB}buff[index] = c;',
        f'{CPP_TAB}{CPP_TAB}index++;',
        f'{CPP_TAB}}}',
        f'{CPP_TAB}buff[index] = 0;',
        f'{CPP_TAB}return std::string(buff);',
    ]
    return '\n'.join(body_lines)


def _format_unpack_code_signal(message,
                               signal_name):
    signal = message.get_signal_by_name(signal_name)
    if _is_string_signal(signal):
        return _format_unpack_code_string(signal)

    conversion_type_name = 'uint{}_t'.format(signal.type_length)
    fmt = '    uint{}_t {} = 0{};\n'
    pack_content = fmt.format(signal.type_length,
                              signal.snake_name,
                              signal.conversion_type_suffix)
    body_lines = []

    for index, shift, shift_direction, mask in signal.segments(invert_shift=True):
        fmt = '    {} |= unpack_{}_shift<uint{}_t>(buffer_[{}], {}u, 0x{:02x}u);'
        line = fmt.format(signal.snake_name,
                          shift_direction,
                          signal.type_length,
                          index,
                          shift,
                          mask)
        body_lines.append(line)

    if signal.is_signed:
        mask = ((1 << (signal.type_length - signal.length)) - 1)

        if mask != 0:
            mask <<= signal.length
            formatted = SIGN_EXTENSION_FMT.format(name=signal.snake_name,
                                                  shift=signal.length - 1,
                                                  mask=mask,
                                                  suffix=signal.conversion_type_suffix)
            body_lines.extend(formatted.splitlines())

        conversion = '    return static_cast<int{1}_t>({0});'.format(signal.snake_name,
                                                              signal.type_length)
        body_lines.append(conversion)
    else:
        conversion = '    return {0};'.format(signal.snake_name)
        body_lines.append(conversion)

    return pack_content + '\n'.join(body_lines)


def _format_unpack_code_level(message,
                              signal_names):
    """Format one unpack level in a signal tree.

    """
    signal_pack = {}

    for signal_name in signal_names:
        pack = ''
        if isinstance(signal_name, dict):
            print('WARNING: Multiplexed signals are not supported')
        else:
           pack = _format_unpack_code_signal(message,
                                             signal_name)
        signal_pack[signal_name] = pack
    return signal_pack


def _format_unpack_code(message):
    return _format_unpack_code_level(message,
                                     message.signal_tree)


def _generate_message_declaration(message):
    signal_constructors = []
    signal_setters = []
    signal_clearers = []
    signals = []

    for signal in message.signals:
        signal_constructors.append(_generate_signal_declaration(signal, message.name))
        signal_setters.append(f'{CPP_TAB}bool set_{signal.name}(const {_signal_physical_type(signal)}& value);')
        signal_clearers.append(f'{CPP_TAB}void clear_{signal.name}();')
        signals.append(f'    {message.name}_{signal.name} {signal.name};')

    if message.comment is None:
        comment = ''
    else:
        comment = ' * {}\n *\n'.format(message.comment)

    static_vars = f'\n    // Public static accessor for const message attributes (cycle time, ID, etc.)\n' \
                  f'    static const uint32_t cycle_time_ms;\n' \
                  f'    static const uint8_t length;\n' \
                  f'    static const uint32_t ID;\n' \
                  f'    static const uint priority;\n'
    if message.protocol == 'j1939':
        static_vars += f'    static const uint32_t PGN;\n'
    return signal_constructors, comment, signal_setters, signal_clearers, signals, static_vars


def _generate_constructor_params(signal):
    param = f'buffer, "{signal.name}"'

    scale = signal.decimal.scale
    offset = signal.decimal.offset
    formatted_scale = _format_decimal(scale, is_float=True)
    formatted_offset = _format_decimal(offset, is_float=True)

    spn = signal.dbc.attributes['SPN'].value if 'SPN' in signal.dbc.attributes else '0'
    unit = '""' if signal.unit == '-' else f'"{signal.unit}"'

    if not (offset == 0 and scale == 1 and unit == '""' and spn == '0'):
        param += f', {offset}, {scale}, {unit}, {spn}'
    return param


def _generate_is_in_range(message):
    """Generate range checks for all signals in given message.
    'true' is returned in place of range check string if minimum/maximum are missing from signal definition
    """

    checks = []

    for signal in message.signals:
        if _is_string_signal(signal):
            checks.append('true')
            continue

        scale = signal.decimal.scale
        offset = (signal.decimal.offset / scale)
        minimum = signal.decimal.minimum
        maximum = signal.decimal.maximum

        if minimum is not None:
            minimum = (minimum / scale - offset)

        if maximum is not None:
            maximum = (maximum / scale - offset)

        if minimum is None and signal.minimum_value is not None:
            if signal.minimum_value > signal.minimum_type_value:
                minimum = signal.minimum_value

        if maximum is None and signal.maximum_value is not None:
            if signal.maximum_value < signal.maximum_type_value:
                maximum = signal.maximum_value

        suffix = signal.type_suffix
        check = []

        if minimum is not None:
            if not signal.is_float:
                minimum = Decimal(int(minimum))

            minimum_type_value = signal.minimum_type_value

            if (minimum_type_value is None) or (minimum > minimum_type_value):
                minimum = _format_decimal(minimum, signal.is_float)
                check.append('(value >= {}{})'.format(minimum, suffix))

        if maximum is not None:
            if not signal.is_float:
                maximum = Decimal(int(maximum))

            maximum_type_value = signal.maximum_type_value

            if (maximum_type_value is None) or (maximum < maximum_type_value):
                maximum = _format_decimal(maximum, signal.is_float)
                check.append('(value <= {}{})'.format(maximum, suffix))

        if not check:
            check = ['true']
        elif len(check) == 1:
            check = [check[0][1:-1]]

        check = ' && '.join(check)

        checks.append(check)

    return checks


def _format_enum_name(value: AnyStr) -> AnyStr:
    """
    Convert an arbitrary string to camelCase with a 'k' prefix
    i.e. "I'm_a C0nst" -> "kImAC0nst"
    """
    caps_alphanumeric = [token.capitalize() for token in re.split(r'[^a-zA-Z0-9]', value)]
    return f'k{"".join(caps_alphanumeric)}'


def _generate_choices(signal):
    if not signal.choices:
        return ''

    choices = ["// Static enum values"]
    for value, name in sorted(signal.unique_choices.items()):
        var_type = 'int' if signal.is_signed else 'uint'
        choices.append(f'static constexpr {var_type} {_format_enum_name(name)} = {value};')

    return '\n    '.join(choices) + '\n'


def _generate_declarations(database_name, messages):
    classes = []

    for message in messages:
        signal_constructors, comment, signal_setters, signal_clearers, signals, static_vars = _generate_message_declaration(message)
        classes.append(
            MESSAGE_DECLARATION_FMT.format(
                signal_constructors='\n'.join(signal_constructors),
                comment=comment,
                database_message_name=message.name,
                message_name=message.snake_name,
                signal_setters='\n'.join(signal_setters),
                signal_clearers='\n'.join(signal_clearers),
                signals='\n'.join(signals),
                static_vars=static_vars))

    return '\n'.join(classes)


def _compute_priority(id: int):
    PRIORITY_OFFSET = 26
    PRIORITY_MASK = 0x1C000000
    return (id & PRIORITY_MASK) >> PRIORITY_OFFSET


def _compute_pgn(id: int):
    RESERVED_OFFSET = 25
    RESERVED_OFFSET_PGN = 17
    RESERVED_MASK = 0x02000000

    DATA_PAGE_OFFSET = 24
    DATA_PAGE_OFFSET_PGN = 16
    DATA_PAGE_MASK = 0x01000000

    PDU_SPECIFIC_OFFSET = 8
    PDU_SPECIFIC_MASK = 0xff00

    PDU_FORMAT_OFFSET = 16
    PDU_FORMAT_OFFSET_PGN = 8
    PDU_FORMAT_MASK = 0xff0000

    GROUP_EXTENSION_OFFSET_PGN = 0

    reserved = (id & RESERVED_MASK) >> RESERVED_OFFSET
    data_page = (id & DATA_PAGE_MASK) >> DATA_PAGE_OFFSET
    pdu_specific = (id & PDU_SPECIFIC_MASK) >> PDU_SPECIFIC_OFFSET
    pdu_format = (id & PDU_FORMAT_MASK) >> PDU_FORMAT_OFFSET

    if pdu_format < 240:    # PDU1
        group_extension = 0
    else:                   # PDU2
        group_extension = pdu_specific

    pgn = 0
    pgn |= (group_extension << GROUP_EXTENSION_OFFSET_PGN) | (pdu_format << PDU_FORMAT_OFFSET_PGN) | \
           (data_page << DATA_PAGE_OFFSET_PGN) | (reserved << RESERVED_OFFSET_PGN)
    return f'{hex(pgn)}'


def _signal_ostream_body(message_name, signal):

    if signal.choices and signal.unit.lower() == 'enum':
        ostream_body = ''
        for value, name in sorted(signal.unique_choices.items()):
            # First unique choice
            if name == list(signal.unique_choices.values())[0]:
                ostream_body += f'{CPP_TAB}if (signal.Real() == {message_name}_{signal.name}::{_format_enum_name(name)}) {{'
                ostream_body += f'\n{CPP_TAB}{CPP_TAB}os << "' + _format_enum_name(name).split('k', 1)[1] + '";'
            # All other choices
            else:
                ostream_body += f'\n{CPP_TAB}}} else if (signal.Real() == {message_name}_{signal.name}::{_format_enum_name(name)}) {{'
                ostream_body += f'\n{CPP_TAB}{CPP_TAB}os << "' + _format_enum_name(name).split('k', 1)[1] + '";'
        ostream_body += f'\n{CPP_TAB}}} else {{\n{CPP_TAB}{CPP_TAB}os << "UNDEFINED";\n{CPP_TAB}}}'
    else:
        if signal.unit.lower() != 'bool':
            ostream_body = f'{CPP_TAB}os << signal.Real()'
        else:
            # TODO static_cast<bool> around signal until bool is a PhysicalDataType option
            ostream_body = f'{CPP_TAB}os << std::boolalpha << static_cast<bool>(signal.Real()) << std::noboolalpha'
        if signal.unit.lower() != 'string' and signal.unit.lower() != 'str' and signal.unit.lower() != 'enum' and \
           signal.unit.lower() != 'bool' and signal.unit != ' ' and signal.unit != '' and signal.unit != '-':
            ostream_body += f' << " " << signal.data_format()'
        ostream_body += ';'
    return ostream_body

def _message_ostream(message):
    ostream_body = f'    os << '
    for signal in message.signals:
        ostream_body += f'"{signal.name}: " << frame.{signal.name}'
        if signal != message.signals[-1]:
            ostream_body += ' << "  " << '
    ostream_body += ';'

    return MESSAGE_DEFINITION_OSTREAM_FMT.format(
        database_message_name=message.name,
        contents=ostream_body)


def _generate_definitions(database_name, messages):
    definitions = []

    for message in messages:
        definition = ''
        signals_in_msg_constructor = []
        signal_definitions = []
        signal_setters = []
        signal_clearers = []

        range_checks = _generate_is_in_range(message)
        pack = _format_pack_code(message)
        clear = _format_clear_code(message)
        unpack = _format_unpack_code(message)

        for signal_iter, signal in enumerate(message.signals):
            signal_definition = f'// Signal {message.name}.{signal.name}\n'

            signal_msg_constructor = f'{CPP_TAB}  {signal.name}(buffer_)'
            # Commas after every member variable initializer except last
            if signal != message.signals[-1]:
                signal_msg_constructor += ','
            signals_in_msg_constructor.append(signal_msg_constructor)

            signal_definition += SIGNAL_DEFINITION_FMT.format(
                name=signal.name,
                message_name=message.name,
                constructor_params=_generate_constructor_params(signal))

            signal_definition += SIGNAL_DEFINITION_OSTREAM_FMT.format(
                name=signal.name,
                message_name=message.name,
                contents=_signal_ostream_body(message.name, signal))

            signal_definition += SIGNAL_DEFINITION_RAW_FMT.format(
                name=signal.name,
                message_name=message.name,
                type_name=_signal_raw_type(signal),
                contents = unpack[signal.name])

            signal_definition += SIGNAL_DEFINITION_RAW_IN_RANGE_FMT.format(
                name=signal.name,
                message_name=message.name,
                type_name=_signal_raw_type(signal),
                check=range_checks[signal_iter])

            signal_definitions.append(signal_definition)

            signal_setters.append(SIGNAL_DEFINITION_SET_FMT.format(
                database_message_name=message.name,
                name=signal.name,
                physical_type=_signal_physical_type(signal),
                contents = pack[signal.name]))

            signal_clearers.append(SIGNAL_DEFINITION_CLEAR_FMT.format(
                database_message_name=message.name,
                name=signal.name,
                contents = clear[signal.name]))

        cycle_time = message.cycle_time if message.cycle_time else '0'
        frame_id = '0x{:02x}'.format(message.frame_id)
        constructor = f'// Message {message.name}\n'
        constructor += MESSAGE_CONSTRUCTOR_DEFINITION_FMT.format(
            database_message_name=message.name,
            id=frame_id,
            length=message.length,
            extended=str(message.is_extended_frame).lower(),
            cycle_time=cycle_time,
            signals='\n'.join(signals_in_msg_constructor))

        static_vars = f'const uint32_t {message.name}::cycle_time_ms = {cycle_time};\n'
        static_vars += f'const uint8_t {message.name}::length = {message.length}u;\n'
        static_vars += f'const uint32_t {message.name}::ID = {frame_id}u;\n'
        static_vars += f'const uint {message.name}::priority = {_compute_priority(message.frame_id)};\n'
        if message.protocol == 'j1939':
            static_vars += f'const uint32_t {message.name}::PGN = {_compute_pgn(message.frame_id)};\n'

        definition = MESSAGE_DEFINITION_FMT.format(
            signal_definitions='\n'.join(signal_definitions),
            constructor=constructor,
            ostream=_message_ostream(message),
            static_vars=static_vars,
            signal_setters='\n'.join(signal_setters),
            signal_clearers='\n'.join(signal_clearers))

        definitions.append(definition)

    return '\n'.join(definitions)


def generate(database,
             database_name,
             header_name,
             source_name):
    """Generate C++ source code from given CAN database `database`.

    `database_name` is used as a prefix for all defines, data
    structures and functions.

    `header_name` is the file name of the C header file, which is
    included by the C source file.

    `source_name` is the file name of the C source file, which is
    needed by the fuzzer makefile.

    This function returns a tuple of the C header and source files as
    strings.
    """
    date = time.ctime()
    messages = [Message(message) for message in database.messages]
    include_guard = 'CANTOOLS_{}_H'.format(database_name.upper())
    declarations = _generate_declarations(database_name, messages)

    definitions = _generate_definitions(database_name, messages)

    header = HEADER_FMT.format(version=__version__,
                               date=date,
                               include_guard=include_guard,
                               declarations=declarations)

    source = SOURCE_FMT.format(version=__version__,
                               date=date,
                               header=header_name,
                               definitions=definitions)

    return header, source
