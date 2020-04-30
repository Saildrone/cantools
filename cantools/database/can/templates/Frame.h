#pragma once

#include <stdint.h>
#include <string>

template<typename data_type>
uint8_t pack_left_shift(data_type value, uint8_t shift, uint8_t mask)
{
    return static_cast<uint8_t>(static_cast<uint8_t>(value << shift) & mask);
}

template<typename data_type>
uint8_t pack_right_shift(data_type value, uint8_t shift, uint8_t mask)
{
    return static_cast<uint8_t>(static_cast<uint8_t>(value >> shift) & mask);
}

template<typename data_type>
data_type unpack_left_shift(uint8_t value, uint8_t shift, uint8_t mask)
{
    return static_cast<data_type>(static_cast<data_type>(value & mask) << shift);
}

template<typename data_type>
data_type unpack_right_shift(uint8_t value, uint8_t shift, uint8_t mask)
{
    return static_cast<data_type>(static_cast<data_type>(value & mask) >> shift);
}

class Frame {
public:
    Frame(uint32_t id, std::string name, uint32_t size, bool extended, uint32_t cycle_time)
        : _id(id)
        , _name(name)
        , _size(size)
        , _extended(extended)
        , _cycle_time(cycle_time)
    {}

    uint32_t id() const { return _id; }
    std::string name() const { return _name; }  // do we want this
    uint32_t size() const { return _size; }
    bool extended() const { return _extended; }
    bool standard() const { return !_extended; }
    uint32_t cycle_time() const { return _cycle_time; }

private:
    // Message ID/Frame ID
    uint32_t _id {};

    // Message name
    std::string _name {};

    // Message length, bytes
    uint32_t _size {};

    // Extended or standard frame type
    bool _extended {false};

    // Message cycle time [ms]
    uint32_t _cycle_time {};
};
