// Introducing google test because cannot get nala to build with bazel - too much effort for too little reward
// to create interopability between python, c, make, and bazel
#include <gtest/gtest.h>

#include <sstream>

#include "css__electronics_sae_j1939_demo.h"
#include "motohawk.h"
#include "string_signals.h"
#include "signed.h"
#include "vehicle.h"

TEST(GenerateCpp, test_ClearSignals_VehicleDBC) {
    RT_DL1MK3_Speed s;
    EXPECT_TRUE(s.set_Validity_Speed(1));
    EXPECT_TRUE(s.set_Accuracy_Speed(100));
    EXPECT_TRUE(s.set_Speed(-5555));

    EXPECT_EQ(s.Speed.Real(), -5555);
    EXPECT_EQ(s.Accuracy_Speed.Real(), 100);
    EXPECT_EQ(s.Validity_Speed.Real(), 1);

    s.clear_Accuracy_Speed();
    EXPECT_EQ(s.Speed.Real(), -5555);
    EXPECT_EQ(s.Accuracy_Speed.Real(), 0);
    EXPECT_EQ(s.Validity_Speed.Real(), 1);

    EXPECT_TRUE(s.set_Accuracy_Speed(10));
    s.clear_Speed();
    EXPECT_EQ(s.Speed.Real(), 0);
    EXPECT_EQ(s.Accuracy_Speed.Real(), 10);
    EXPECT_EQ(s.Validity_Speed.Real(), 1);
}

TEST(GenerateCpp, test_SetSignalsMultipleTimes_VehicleDBC) {
    RT_DL1MK3_Speed s;
    EXPECT_TRUE(s.set_Validity_Speed(1));
    EXPECT_TRUE(s.set_Accuracy_Speed(100));
    EXPECT_TRUE(s.set_Speed(-5555));

    EXPECT_EQ(s.Speed.Real(), -5555);
    EXPECT_EQ(s.Accuracy_Speed.Real(), 100);
    EXPECT_EQ(s.Validity_Speed.Real(), 1);

    EXPECT_TRUE(s.set_Speed(5555));
    EXPECT_TRUE(s.set_Accuracy_Speed(222));
    EXPECT_TRUE(s.set_Validity_Speed(0));

    EXPECT_EQ(s.Speed.Real(), 5555);
    EXPECT_EQ(s.Accuracy_Speed.Real(), 222);
    EXPECT_EQ(s.Validity_Speed.Real(), 0);

    EXPECT_TRUE(s.set_Speed(0));
    EXPECT_TRUE(s.set_Accuracy_Speed(0));
    EXPECT_TRUE(s.set_Validity_Speed(1));

    EXPECT_EQ(s.Speed.Real(), 0);
    EXPECT_EQ(s.Accuracy_Speed.Real(), 0);
    EXPECT_EQ(s.Validity_Speed.Real(), 1);

    RT_SB_INS_Vel_Body_Axes m;
    EXPECT_TRUE(m.set_Validity_INS_Vel_Forwards(0));
    EXPECT_TRUE(m.set_Validity_INS_Vel_Sideways(1));
    EXPECT_TRUE(m.set_Accuracy_INS_Vel_Body(249));
    EXPECT_TRUE(m.set_INS_Vel_Forwards_2D(-100));
    EXPECT_TRUE(m.set_INS_Vel_Sideways_2D(100));

    EXPECT_EQ(m.Validity_INS_Vel_Forwards.Real(), 0);
    EXPECT_EQ(m.Validity_INS_Vel_Sideways.Real(), 1);
    EXPECT_EQ(m.Accuracy_INS_Vel_Body.Real(), 249);
    EXPECT_EQ(m.INS_Vel_Forwards_2D.Real(), -100);
    EXPECT_EQ(m.INS_Vel_Sideways_2D.Real(), 100);

    EXPECT_TRUE(m.set_Validity_INS_Vel_Forwards(1));
    EXPECT_TRUE(m.set_Validity_INS_Vel_Sideways(0));
    EXPECT_TRUE(m.set_Accuracy_INS_Vel_Body(50));
    EXPECT_TRUE(m.set_INS_Vel_Forwards_2D(100));
    EXPECT_TRUE(m.set_INS_Vel_Sideways_2D(-100));

    EXPECT_EQ(m.Validity_INS_Vel_Forwards.Real(), 1);
    EXPECT_EQ(m.Validity_INS_Vel_Sideways.Real(), 0);
    EXPECT_EQ(m.Accuracy_INS_Vel_Body.Real(), 50);
    EXPECT_EQ(m.INS_Vel_Forwards_2D.Real(), 100);
    EXPECT_EQ(m.INS_Vel_Sideways_2D.Real(), -100);
}

// Copy struct pack/unpack in test_basic.motohawk_example_message_t
TEST(GenerateCpp, test_StructUnpack_MotohawkDBC) {
    uint8_t buffer[] = "\xc0\x06\xe0\x00\x00\x00\x00\x00";
    ExampleMessage m(buffer, 8u);

    // Confirm unpacking values is successful
    EXPECT_EQ(1, m.Enable.Raw());
    EXPECT_EQ(32, m.AverageRadius.Raw());
    EXPECT_EQ(55, m.Temperature.Raw());

    // Confirm buffer HexString() accuracy
    auto hstr = m.HexString();
    EXPECT_EQ(hstr, "c006e00000000000");

    auto bstr = m.BinaryString();
    std::cout << bstr << std::endl;
    EXPECT_EQ(bstr, "11000000 00000110 11100000 00000000 00000000 00000000 00000000 00000000");

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

TEST(GenerateCpp, test_StructPack_MotohawkDBC) {
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

TEST(GenerateCpp, test_StructPack_SignedDBC) {
    Message64 m;

    EXPECT_TRUE(m.set_s64(-5));
    EXPECT_EQ(-5, m.s64.Raw());
    EXPECT_EQ(-5, m.s64.Real());
    EXPECT_EQ("fbffffffffffffff", m.HexString());
    EXPECT_EQ("11111011 11111111 11111111 11111111 11111111 11111111 11111111 11111111", m.BinaryString());

    m.Clear();
    EXPECT_EQ("0000000000000000", m.HexString());
    EXPECT_EQ("00000000 00000000 00000000 00000000 00000000 00000000 00000000 00000000", m.BinaryString());

}

TEST(GenerateCpp, test_SPNs_CSSElectronicsSAEJ1939DBC) {
    EEC1 eec1;
    CCVS1 ccvs1;

    EXPECT_EQ(eec1.EngineSpeed.spn(), 190);
    EXPECT_EQ(ccvs1.WheelBasedVehicleSpeed.spn(), 84);

    // Test static member vars
    EXPECT_EQ(EEC1::cycle_time_ms, 500);
    EXPECT_EQ(CCVS1::ID, 0x18fef1fe);
    EXPECT_EQ(CCVS1::PGN, 0xfef1);
}

TEST(GenerateCpp, test_OstreamOperator_MotohawkDBC) {
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

TEST(GenerateCpp, test_SignalStringType_StringDBC) {
    PersonName full_name;
    full_name.set_first_name("Johnathan");
    full_name.set_last_name("Doe");
    full_name.set_height(67);
    full_name.set_age(26);
    full_name.set_alive(true);

    std::stringstream os;
    os << full_name.first_name;
    EXPECT_EQ(os.str(), "Johnathan");

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
    os << full_name.alive;
    EXPECT_EQ(os.str(), "true");

    os.str(std::string());
    os << full_name;
    EXPECT_EQ(os.str(), "first_name: Johnathan  age: 26 years  last_name: Doe  height: 67 inches  alive: true");

    PersonName too_long;
    too_long.set_first_name("Thisnameislongerthantwentycharacterssoitshouldtruncate");
    EXPECT_EQ(too_long.first_name.Real(), "Thisnameislongerthan");
}

int main(int argc, char **argv) {
    ::testing::InitGoogleTest(&argc, argv);
    return RUN_ALL_TESTS();
}
