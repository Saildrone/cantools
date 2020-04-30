// Introducing google test because cannot get nala to build with bazel - too much effort for too little reward
// to create interopability between python, c, make, and bazel
#include <gtest/gtest.h>

#include "motohawk.h"

// Copy struct pack/unpack in test_basic.motohawk_example_message_t
TEST(motohawk, struct_unpack) {
    uint8_t buffer[] = {"\xc0\x06\xe0\x00\x00\x00\x00\x00"};
    ExampleMessage m(&buffer[0], 8u);
    EXPECT_EQ(1, m.Enable_raw());
    EXPECT_EQ(32, m.AverageRadius_raw());
    EXPECT_EQ(55, m.Temperature_raw());
}

TEST(motohawk, struct_pack) {
    uint8_t buffer[8];
    ExampleMessage m(&buffer[0], 8u);
    // TODO if this buffer isn't cleared/initialized then the test will fail
    // Can this be handled in constructor? Or leave to client to initalize mem for buffer
    m.clear();
    
    // Set Enable and confirm
    EXPECT_TRUE(m.set_Enable(1));
    EXPECT_EQ(1, m.Enable());

    // Set Radius and confirm Enable and AverageRadius signals
    EXPECT_TRUE(m.set_AverageRadius(0.5));
    EXPECT_EQ(1, m.Enable());
    EXPECT_EQ(0.5, m.AverageRadius());

    // Set Temperature and confirm Enable, AverageRadius, and Temperature signals
    EXPECT_TRUE(m.set_Temperature(250));
    EXPECT_EQ(1, m.Enable());
    EXPECT_EQ(0.5, m.AverageRadius());
    EXPECT_EQ(250, m.Temperature());
}

int main(int argc, char **argv) {
    ::testing::InitGoogleTest(&argc, argv);
    return RUN_ALL_TESTS();
}
