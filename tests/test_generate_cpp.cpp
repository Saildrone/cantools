// Introducing google test because cannot get nala to build with bazel - too much effort for too little reward
// to create interopability between python, c, make, and bazel
#include <gtest/gtest.h>

#include "motohawk.h"

// Copy struct pack/unpack in test_basic.motohawk_example_message_t
TEST(motohawk, struct_unpack) {
    uint8_t buffer[] = "\xc0\x06\xe0\x00\x00\x00\x00\x00";
    ExampleMessage m(buffer, 8u);
    EXPECT_EQ(1, m.Enable.raw());
    EXPECT_EQ(32, m.AverageRadius.raw());
    EXPECT_EQ(55, m.Temperature.raw());
    auto str = m.to_string();
    EXPECT_EQ(str, "c006e00000000000");
    
    auto output_buffer = m.buffer();
    for (size_t i = 0; i < 8; ++i) {
        EXPECT_EQ(buffer[i], output_buffer[i]);
    }

    EXPECT_TRUE(m.set_Enable(0));
    EXPECT_TRUE(m.set_AverageRadius(0.5));
    EXPECT_TRUE(m.set_Temperature(249));
    auto output_buffer2 = m.buffer();
    for (size_t i = 0; i < 8; ++i) {
        EXPECT_EQ(buffer[i], output_buffer2[i]);
    }
}

TEST(motohawk, struct_pack) {
    ExampleMessage m;

    // Set Enable and confirm
    EXPECT_TRUE(m.set_Enable(1));
    EXPECT_EQ(1, m.Enable.real());

    // Set Radius and confirm Enable and AverageRadius signals
    EXPECT_TRUE(m.set_AverageRadius(0.5));
    EXPECT_EQ(1, m.Enable.real());
    EXPECT_EQ(0.5, m.AverageRadius.real());

    // Set Temperature and confirm Enable, AverageRadius, and Temperature signals
    EXPECT_TRUE(m.set_Temperature(250));
    EXPECT_EQ(1, m.Enable.real());
    EXPECT_EQ(0.5, m.AverageRadius.real());
    EXPECT_EQ(250, m.Temperature.real());
}

int main(int argc, char **argv) {
    ::testing::InitGoogleTest(&argc, argv);
    return RUN_ALL_TESTS();
}
