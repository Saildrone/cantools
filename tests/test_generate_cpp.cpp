// Introducing google test because cannot get nala to build with bazel - too much effort for too little reward
// to create interopability between python, c, make, and bazel
#include <gtest/gtest.h>

#include <sstream>

#include "motohawk.h"
#include "string_signals.h"
#include "signed.h"
#include "css__electronics_sae_j1939_demo.h"

// Copy struct pack/unpack in test_basic.motohawk_example_message_t
TEST(GenerateCpp, test_StructUnpack_Motohawk_DBC) {
    uint8_t buffer[] = "\xc0\x06\xe0\x00\x00\x00\x00\x00";
    ExampleMessage m(buffer, 8u);

    // Confirm unpacking values is successful
    EXPECT_EQ(1, m.Enable.Raw());
    EXPECT_EQ(32, m.AverageRadius.Raw());
    EXPECT_EQ(55, m.Temperature.Raw());

    // Confirm buffer ToString() accuracy
    auto str = m.ToString();
    EXPECT_EQ(str, "c006e00000000000");
    
    // Confirm input buffer equal to buffer accessor
    auto output_buffer = m.buffer();
    for (size_t i = 0; i < 8; ++i) {
        EXPECT_EQ(buffer[i], output_buffer[i]);
    }

    // Confirm after setting new signals values that original buffer pointer is modified
    EXPECT_TRUE(m.set_Enable(0));
    EXPECT_TRUE(m.set_AverageRadius(0.5));
    EXPECT_TRUE(m.set_Temperature(249));
    output_buffer = m.buffer();
    for (size_t i = 0; i < 8; ++i) {
        EXPECT_EQ(buffer[i], output_buffer[i]);
    }
}

TEST(GenerateCpp, test_StructPack_Motohawk_DBC) {
    ExampleMessage m;

    // Set Enable and confirm
    EXPECT_TRUE(m.set_Enable(1));
    EXPECT_EQ(1, m.Enable.Real());

    // Set Radius and confirm Enable and AverageRadius signals
    EXPECT_TRUE(m.set_AverageRadius(0.5));
    EXPECT_EQ(1, m.Enable.Real());
    EXPECT_EQ(0.5, m.AverageRadius.Real());

    // Set Temperature and confirm Enable, AverageRadius, and Temperature signals
    EXPECT_TRUE(m.set_Temperature(250));
    EXPECT_EQ(1, m.Enable.Real());
    EXPECT_EQ(0.5, m.AverageRadius.Real());
    EXPECT_EQ(250, m.Temperature.Real());
}

TEST(GenerateCpp, test_StructPack_Signed_DBC) {
    Message64 m;

    EXPECT_TRUE(m.set_s64(-5));
    EXPECT_EQ(-5, m.s64.Raw());
    EXPECT_EQ(-5, m.s64.Real());
    EXPECT_EQ("fbffffffffffffff", m.ToString());

    m.Clear();
    EXPECT_EQ("0000000000000000", m.ToString());
}

TEST(GenerateCpp, test_SPNs_CSSElectronicsSAEJ1939_DBC) {
    EEC1 eec1;
    CCVS1 ccvs1;

    EXPECT_EQ(eec1.EngineSpeed.spn(), 190);
    EXPECT_EQ(ccvs1.WheelBasedVehicleSpeed.spn(), 84);
    
    // Test static member vars
    EXPECT_EQ(EEC1::cycle_time_ms, 500);
    EXPECT_EQ(CCVS1::ID, 0x18fef1fe);
    EXPECT_EQ(CCVS1::PGN, 0xfef1);
}

TEST(GenerateCpp, test_OstreamOperator_Motohawk_DBC) {
    ExampleMessage m;
    m.set_Temperature(250);
    m.set_AverageRadius(0.25);
    m.set_Enable(0);

    std::stringstream os;
    os << m.AverageRadius;
    EXPECT_EQ(os.str(), "0.2 m");
    
    os.str(std::string());
    os << m.Temperature;
    EXPECT_EQ(os.str(), "250 degK");

    os.str(std::string());
    os << m.Enable;
    EXPECT_EQ(os.str(), "0");

    os.str(std::string());
    os << m;
    EXPECT_EQ(os.str(), "Enable: 0  AverageRadius: 0.2 m  Temperature: 250 degK");
}

TEST(GenerateCpp, test_SignalStringType_String_DBC) {
    PersonName full_name;
    full_name.set_first_name("John");
    full_name.set_last_name("Doe");
    full_name.set_height(67);
    full_name.set_age(26);

    std::stringstream os;
    os << full_name.first_name;
    EXPECT_EQ(os.str(), "John");

    os.str(std::string());
    os << full_name.last_name;
    EXPECT_EQ(os.str(), "Doe");

    os.str(std::string());
    os << full_name.height;
    EXPECT_EQ(os.str(), "67 inches");

    os.str(std::string());
    os << full_name.age;
    EXPECT_EQ(os.str(), "26 years");


    os.str(std::string());
    os << full_name;
    EXPECT_EQ(os.str(), "first_name: John  age: 26 years  last_name: Doe  height: 67 inches  _reserved: 0");
}

int main(int argc, char **argv) {
    ::testing::InitGoogleTest(&argc, argv);
    return RUN_ALL_TESTS();
}
