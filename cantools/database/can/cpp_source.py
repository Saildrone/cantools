from __future__ import print_function
import re
import time
from decimal import Decimal

from ...version import __version__


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

#include "Frame.h"

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

{definitions}\
'''

MESSAGE_DECLARATION_FMT = '''\
/**
 * Message {database_message_name}.
 *
{comment}\
 */
class {database_message_name} : public Frame {{
public:
    /** Constructor */
    {database_message_name}(uint8_t* buffer, size_t size);

    {database_message_name}& GetMessage() {{ 
        return *this; 
    }}
 
    uint8_t* buffer() {{
        return _buffer;
    }}
 
    size_t buffer_size() {{
        return _buffer_size;
    }}
  
    // Clear buffer
    void clear();

{members}

private:
    uint8_t* _buffer;
    size_t _buffer_size;

{encode_decode_members}
}};
'''

SIGNAL_DECLARATION_FMT = '''\
    /**
     * Signal {name}.
{comment}\
     * Range: {range}
     * Scale: {scale}
     * Offset: {offset}
{additional_comments}\
     */
    double {name}();
    {type_name} {name}_raw();
    bool set_{name}(const double& value);
    bool {name}_in_range(const double& value);
    bool {name}_raw_in_range(const {type_name}& value) const;
    std::string {name}_data_format() const;
    {additional}\
'''

SIGNAL_ENCODE_DECODE_DECLARATION_FMT = '''\
    {type_name} {name}_encode(double value);
    double {name}_decode({type_name} value);
'''

MESSAGE_DEFINITION_FMT = '''\
{constructor}
{signal_definitions}
'''

MESSAGE_CONSTRUCTOR_DEFINITION_FMT = '''\
{database_message_name}::{database_message_name}(uint8_t* buffer, size_t size)
    : Frame({id}u, "{database_message_name}", {length}u, {extended}, {cycle_time}u)
    , _buffer(buffer)
    , _buffer_size(size)
{{}}
'''

SIGNAL_DEFINITION_FMT = '''\
double {database_message_name}::{name}() {{
{contents}
}}

'''

SIGNAL_DEFINITION_RAW_FMT = '''\
{type_name} {database_message_name}::{name}_raw() {{
{contents}
}}

'''

SIGNAL_DEFINITION_SET_FMT = '''\
bool {database_message_name}::set_{name}(const double& value) {{

{contents}
}}

'''

SIGNAL_DEFINITION_IN_RANGE_FMT = '''\
bool {database_message_name}::{name}_in_range(const double& value) {{
    {type_name} {snake_name} = {name}_encode(value);
    return {name}_raw_in_range({snake_name});
}}

'''

SIGNAL_DEFINITION_RAW_IN_RANGE_FMT = '''\
bool {database_message_name}::{name}_raw_in_range(const {type_name}& value) const {{
    return ({check});
}}

'''

SIGNAL_DEFINITION_DATA_FORMAT_FMT = '''\
std::string {database_message_name}::{name}_data_format() const {{
    return "{data_format}";
}}

'''

SIGNAL_DEFINITION_SPN_FMT = '''\
uint32_t {database_message_name}::{name}_SPN() const {{
    return {spn};
}}

'''

SIGNAL_DEFINITION_ENCODE_DECODE_FMT = '''\
{type_name} {database_message_name}::{name}_encode(double value) {{
    return static_cast<{type_name}>({encode});
}}

double {database_message_name}::{name}_decode({type_name} value) {{
    return ({decode});
}}
'''

SIGN_EXTENSION_FMT = '''
    if (({name} & (1{suffix} << {shift})) != 0{suffix}) {{
        {name} |= 0x{mask:x}{suffix};
    }}

'''


class Signal(object):

    def __init__(self, signal):
        self._signal = signal
        self.snake_name = camel_to_snake_case(self.name)

    def __getattr__(self, name):
        return getattr(self._signal, name)

    @property
    def unit(self):
        return _get(self._signal.unit, '-')

    @property
    def type_length(self):
        if self.length <= 8:
            return 8
        elif self.length <= 16:
            return 16
        elif self.length <= 32:
            return 32
        else:
            return 64

    @property
    def type_name(self):
        if self.is_float:
            if self.length == 32:
                type_name = 'float'
            else:
                type_name = 'double'
        else:
            type_name = 'int{}_t'.format(self.type_length)

            if not self.is_signed:
                type_name = 'u' + type_name

        return type_name

    @property
    def type_suffix(self):
        try:
            return {
                'uint8_t': 'u',
                'uint16_t': 'u',
                'uint32_t': 'u',
                'int64_t': 'll',
                'uint64_t': 'ull',
                'float': 'f'
            }[self.type_name]
        except KeyError:
            return ''

    @property
    def conversion_type_suffix(self):
        try:
            return {
                8: 'u',
                16: 'u',
                32: 'u',
                64: 'ull'
            }[self.type_length]
        except KeyError:
            return ''

    @property
    def unique_choices(self):
        """Make duplicated choice names unique by first appending its value
        and then underscores until unique.

        """

        items = {
            value: camel_to_snake_case(name).upper()
            for value, name in self.choices.items()
        }
        names = list(items.values())
        duplicated_names = [
            name
            for name in set(names)
            if names.count(name) > 1
        ]
        unique_choices = {
            value: name
            for value, name in items.items()
            if names.count(name) == 1
        }

        for value, name in items.items():
            if name in duplicated_names:
                name += _canonical('_{}'.format(value))

                while name in unique_choices.values():
                    name += '_'

                unique_choices[value] = name

        return unique_choices

    @property
    def minimum_type_value(self):
        if self.type_name == 'int8_t':
            return -128
        elif self.type_name == 'int16_t':
            return -32768
        elif self.type_name == 'int32_t':
            return -2147483648
        elif self.type_name == 'int64_t':
            return -9223372036854775808
        elif self.type_name[0] == 'u':
            return 0
        else:
            return None

    @property
    def maximum_type_value(self):
        if self.type_name == 'int8_t':
            return 127
        elif self.type_name == 'int16_t':
            return 32767
        elif self.type_name == 'int32_t':
            return 2147483647
        elif self.type_name == 'int64_t':
            return 9223372036854775807
        elif self.type_name == 'uint8_t':
            return 255
        elif self.type_name == 'uint16_t':
            return 65535
        elif self.type_name == 'uint32_t':
            return 4294967295
        elif self.type_name == 'uint64_t':
            return 18446744073709551615
        else:
            return None

    @property
    def minimum_value(self):
        if self.is_float:
            return None
        elif self.is_signed:
            return -(2 ** (self.length - 1))
        else:
            return 0

    @property
    def maximum_value(self):
        if self.is_float:
            return None
        elif self.is_signed:
            return ((2 ** (self.length - 1)) - 1)
        else:
            return ((2 ** self.length) - 1)

    def segments(self, invert_shift):
        index, pos = divmod(self.start, 8)
        left = self.length

        while left > 0:
            if self.byte_order == 'big_endian':
                if left >= (pos + 1):
                    length = (pos + 1)
                    pos = 7
                    shift = -(left - length)
                    mask = ((1 << length) - 1)
                else:
                    length = left
                    shift = (pos - length + 1)
                    mask = ((1 << length) - 1)
                    mask <<= (pos - length + 1)
            else:
                shift = (left - self.length) + pos

                if left >= (8 - pos):
                    length = (8 - pos)
                    mask = ((1 << length) - 1)
                    mask <<= pos
                    pos = 0
                else:
                    length = left
                    mask = ((1 << length) - 1)
                    mask <<= pos

            if invert_shift:
                if shift < 0:
                    shift = -shift
                    shift_direction = 'left'
                else:
                    shift_direction = 'right'
            else:
                if shift < 0:
                    shift = -shift
                    shift_direction = 'right'
                else:
                    shift_direction = 'left'

            yield index, shift, shift_direction, mask

            left -= length
            index += 1


class Message(object):

    def __init__(self, message):
        self._message = message
        self.snake_name = camel_to_snake_case(self.name)
        self.signals = [Signal(signal)for signal in message.signals]

    def __getattr__(self, name):
        return getattr(self._message, name)

    def get_signal_by_name(self, name):
        for signal in self.signals:
            if signal.name == name:
                return signal


def _canonical(value):
    """Replace anything but 'a-z', 'A-Z' and '0-9' with '_'.

    """

    return re.sub(r'[^a-zA-Z0-9]', '_', value)


def camel_to_snake_case(value):
    value = re.sub(r'(.)([A-Z][a-z]+)', r'\1_\2', value)
    value = re.sub(r'(_+)', '_', value)
    value = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', value).lower()
    value = _canonical(value)

    return value


def _strip_blank_lines(lines):
    try:
        while lines[0] == '':
            lines = lines[1:]

        while lines[-1] == '':
            lines = lines[:-1]
    except IndexError:
        pass

    return lines


def _get(value, default):
    if value is None:
        value = default

    return value


def _format_comment(comment):
    if comment:
        return '\n'.join([
            '     * ' + line.rstrip()
            for line in comment.splitlines()
        ]) + '\n     *\n'
    else:
        return ''


def _format_decimal(value, is_float=False):
    if int(value) == value:
        value = int(value)

        if is_float:
            return str(value) + '.0'
        else:
            return str(value)
    else:
        return str(value)


def _format_range(signal):
    minimum = signal.decimal.minimum
    maximum = signal.decimal.maximum
    scale = signal.decimal.scale
    offset = signal.decimal.offset

    if minimum is not None and maximum is not None:
        return '{}..{} ({}..{} {})'.format(
            _format_decimal((minimum - offset) / scale),
            _format_decimal((maximum - offset) / scale),
            minimum,
            maximum,
            signal.unit)
    elif minimum is not None:
        return '{}.. ({}.. {})'.format(
            _format_decimal((minimum - offset) / scale),
            minimum,
            signal.unit)
    elif maximum is not None:
        return '..{} (..{} {})'.format(
            _format_decimal((maximum - offset) / scale),
            maximum,
            signal.unit)
    else:
        return '-'


def _generate_signal_declaration(signal):
    comment = _format_comment(signal.comment)
    range_ = _format_range(signal)
    scale = _get(signal.scale, '-')
    offset = _get(signal.offset, '-')
    additional_comments = ''
    additional = ''

    if 'SPN' in signal.dbc.attributes:
        additional = 'uint32_t {name}_SPN() const;'.format(name=signal.name)
        additional_comments += 'SPN: {spn}'.format(spn=signal.dbc.attributes['SPN'].value)

    member = SIGNAL_DECLARATION_FMT.format(comment=comment,
                                           range=range_,
                                           scale=scale,
                                           offset=offset,
                                           additional_comments=_format_comment(additional_comments),
                                           name=signal.name,
                                           type_name=signal.type_name,
                                           additional=additional)
    return member


def _generate_signal_encode_decode_declaration(signal):
    return SIGNAL_ENCODE_DECODE_DECLARATION_FMT.format(
        type_name=signal.type_name,
        name=signal.name)


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


def _format_pack_code_signal(message,
                             signal_name):
    signal = message.get_signal_by_name(signal_name)
    fmt = '\tuint{}_t {} = {}_encode(value);\n'
    pack_content = fmt.format(signal.type_length,
                              signal.snake_name,
                              signal.name)

    body_lines = []
    body_lines.append(f'\tif (!{signal.name}_raw_in_range({signal.snake_name})) {{\n\t\treturn false;\n\t}}')

    for index, shift, shift_direction, mask in signal.segments(invert_shift=False):
        fmt = '\t_buffer[{}] |= pack_{}_shift<uint{}_t>({}, {}u, 0x{:02x}u);'
        line = fmt.format(index,
                          shift_direction,
                          signal.type_length,
                          signal.snake_name,
                          shift,
                          mask)
        body_lines.append(line)
    body_lines.append('\treturn true;')
    return pack_content + '\n'.join(body_lines) 


def _format_pack_code_level(message,
                            signal_names):
    """Format one pack level in a signal tree.
    """
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


def _format_pack_code(message):
    return _format_pack_code_level(message,
                                   message.signal_tree)


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


def _format_unpack_code_signal(message,
                               signal_name):
    signal = message.get_signal_by_name(signal_name)
    conversion_type_name = 'uint{}_t'.format(signal.type_length)
    fmt = '\tuint{}_t {} = 0{};\n'
    pack_content = fmt.format(signal.type_length,
                              signal.snake_name,
                              signal.conversion_type_suffix)
    body_lines = []

    for index, shift, shift_direction, mask in signal.segments(invert_shift=True):
        fmt = '    {} |= unpack_{}_shift<uint{}_t>(_buffer[{}], {}u, 0x{:02x}u);'
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
    members = []
    encode_decode_members = []

    for signal in message.signals:
        members.append(_generate_signal_declaration(signal))
        encode_decode_members.append(_generate_signal_encode_decode_declaration(signal))

    if not members:
        members = [
            '    /**\n'
            '     * Dummy signal in empty message.\n'
            '     */\n'
            '    uint8_t dummy;'
        ]

    if message.comment is None:
        comment = ''
    else:
        comment = ' * {}\n *\n'.format(message.comment)

    return comment, members, encode_decode_members


def _format_choices(signal, signal_name):
    choices = []

    for value, name in sorted(signal.unique_choices.items()):
        if signal.is_signed:
            fmt = '{signal_name}_{name}_CHOICE ({value})'
        else:
            fmt = '{signal_name}_{name}_CHOICE ({value}u)'

        choices.append(fmt.format(signal_name=signal_name.upper(),
                                  name=name,
                                  value=value))

    return choices


def _generate_encode_decode(message):
    encode_decode = []

    for signal in message.signals:
        scale = signal.decimal.scale
        offset = signal.decimal.offset
        formatted_scale = _format_decimal(scale, is_float=True)
        formatted_offset = _format_decimal(offset, is_float=True)

        if offset == 0 and scale == 1:
            encoding = 'value'
            decoding = '(double)value'
        elif offset != 0 and scale != 1:
            encoding = '(value - {}) / {}'.format(formatted_offset,
                                                  formatted_scale)
            decoding = '(static_cast<double>(value) * {}) + {}'.format(formatted_scale,
                                                          formatted_offset)
        elif offset != 0:
            encoding = 'value - {}'.format(formatted_offset)
            decoding = 'static_cast<double>(value) + {}'.format(formatted_offset)
        else:
            encoding = 'value / {}'.format(formatted_scale)
            decoding = 'static_cast<double>(value) * {}'.format(formatted_scale)

        encode_decode.append((encoding, decoding))

    return encode_decode


def _generate_is_in_range(message):
    """Generate range checks for all signals in given message.
    'true' is returned in place of range check string if minimum/maximum are missing from signal definition
    """

    checks = []

    for signal in message.signals:
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


def _generate_choices_defines(database_name, messages):
    choices_defines = []

    for message in messages:
        for signal in message.signals:
            if signal.choices is None:
                continue

            choices = _format_choices(signal, signal.snake_name)
            signal_choices_defines = '\n'.join([
                '#define {}_{}_{}'.format(database_name.upper(),
                                          message.snake_name.upper(),
                                          choice)
                for choice in choices
            ])
            choices_defines.append(signal_choices_defines)

    return '\n\n'.join(choices_defines)


def _generate_declarations(database_name, messages):
    classes = []

    for message in messages:
        comment, members, encode_decode_members = _generate_message_declaration(message)
        classes.append(
            MESSAGE_DECLARATION_FMT.format(
                comment=comment,
                database_message_name=message.name,
                message_name=message.snake_name,
                database_name=database_name,
                members='\n\n'.join(members),
                encode_decode_members='\n'.join(encode_decode_members)))
        
    return '\n'.join(classes)


def _generate_definitions(database_name, messages):
    definitions = []

    for message in messages:
        definition = ''
        signal_definitions = []

        constructor = f'// Message {message.name}\n'
        constructor += MESSAGE_CONSTRUCTOR_DEFINITION_FMT.format(
            database_message_name=message.name,
            id='0x{:02x}'.format(message.frame_id),
            length=message.length,
            extended=str(message.is_extended_frame).lower(),
            cycle_time=message.cycle_time if message.cycle_time else '0') 

        range_checks = _generate_is_in_range(message)
        encode_decode = _generate_encode_decode(message)

        pack = _format_pack_code(message)
        unpack = _format_unpack_code(message)

        for signal_iter, signal in enumerate(message.signals):
            signal_definition = f'// {message.name}.{signal.name}\n'

            signal_definition += SIGNAL_DEFINITION_FMT.format(
                database_message_name=message.name,
                name=signal.name,
                contents=f'\treturn {signal.name}_decode({signal.name}_raw());')

            signal_definition += SIGNAL_DEFINITION_RAW_FMT.format(
                database_message_name=message.name,
                name=signal.name,
                type_name=signal.type_name,
                contents = unpack[signal.name])

            signal_definition += SIGNAL_DEFINITION_SET_FMT.format(
                database_message_name=message.name,
                name=signal.name,
                contents = pack[signal.name])

            signal_definition += SIGNAL_DEFINITION_IN_RANGE_FMT.format(
                database_message_name=message.name,
                name=signal.name,
                type_name=signal.type_name,
                snake_name=signal.snake_name)

            signal_definition += SIGNAL_DEFINITION_RAW_IN_RANGE_FMT.format(
                database_message_name=message.name,
                name=signal.name,
                type_name=signal.type_name,
                check=range_checks[signal_iter])

            signal_definition += SIGNAL_DEFINITION_DATA_FORMAT_FMT.format(
                database_message_name=message.name,
                name=signal.name,
                data_format='' if signal.unit == '-' else signal.unit)

            if 'SPN' in signal.dbc.attributes:
                signal_definition += SIGNAL_DEFINITION_SPN_FMT.format(
                    database_message_name=message.name,
                    name=signal.name,
                    spn=signal.dbc.attributes['SPN'].value)
            
            signal_definition += SIGNAL_DEFINITION_ENCODE_DECODE_FMT.format(
                database_message_name=message.name,
                name=signal.name,
                type_name=signal.type_name,
                encode=encode_decode[signal_iter][0],
                decode=encode_decode[signal_iter][1])

            signal_definitions.append(signal_definition)

        definition = MESSAGE_DEFINITION_FMT.format(
            constructor=constructor,
            signal_definitions='\n'.join(signal_definitions))
        
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
    include_guard = '{}_H'.format(database_name.upper())
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
