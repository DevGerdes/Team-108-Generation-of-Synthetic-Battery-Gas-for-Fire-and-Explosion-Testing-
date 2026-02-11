#include <stdlib.h>

const uint32_t BAUD = 115200;

int STATE = 0; // Default to emergency stop to close everything down
// MFC Setpoint Values
float MFC1 = 0;
float MFC2 = 0;
float MFC3 = 0;
float MFC4 = 0;
float MFC5 = 0;
// Valve Setpoint Value
int VALVE = 0; // Default closed, 1 = open
// MFC Response Values
float MFC1_RESPONSE = 0;
float MFC2_RESPONSE = 0;
float MFC3_RESPONSE = 0;
float MFC4_RESPONSE = 0;
float MFC5_RESPONSE = 0;
// Sensor Values (hardcoded, independent)
float MixingChamberPressure = 0; 
float PipePressure = 0;
float GasSensor1 = 0;
float GasSensor2 = 0;

// ----- Pin Assignments -----
// MFC Setpoint outputs
const uint8_t MFC1_SET_PIN = A0;
const uint8_t MFC2_SET_PIN = A1;
const uint8_t MFC3_SET_PIN = A2;
const uint8_t MFC4_SET_PIN = A3;
const uint8_t MFC5_SET_PIN = A4;
// MFC Response inputs
const uint8_t MFC1_READ_PIN = A5;
const uint8_t MFC2_READ_PIN = A6;
const uint8_t MFC3_READ_PIN = A7;
const uint8_t MFC4_READ_PIN = A8;
const uint8_t MFC5_READ_PIN = A9;
// Valve set pin
const uint8_t VALVE_SET_PIN = 2; // Digital pin 2 (D2)
// Sensor analog response pins
const uint8_t MixingChamberPressure_PIN = A10;
const uint8_t PipePressure_PIN = A11;
const uint8_t GasSensor1_PIN = A12;
const uint8_t GasSensor2_PIN = A13;
const uint8_t SENSOR5_PIN = A14;


#define OUTBUF_SIZE 160 // Max charecter length for serial out. Makes things truncate safely for sending if too long, and can be increased if needed (shouldnt need to)
char lineBuffer[96];
uint8_t bufPos = 0;

char outBuffer[OUTBUF_SIZE]; // the actual buffered output message
uint32_t seq = 1;


void setup()
{
    Serial.begin(BAUD);
    pinMode(VALVE_SET_PIN, OUTPUT);
    pinMode(LED_BUILTIN,OUTPUT);
}

void loop()
{
    while (Serial.available())
    {
        // Logic to detect new serial data input and run rest of protocol
        char c = Serial.read();
        if (c == '\n')
        {
            digitalWrite(LED_BUILTIN,HIGH);
            delay(250);
            digitalWrite(LED_BUILTIN,LOW);
            lineBuffer[bufPos] = 0; // for serial read logic
            parseLine(lineBuffer); // Read the incoming data and write apply setpoints and logic
            sendLine(); // Reply with newly read MFC response and sensor values
            bufPos = 0;
        }
        else if (c != '\r')
        {
            if (bufPos < sizeof(lineBuffer) - 1)
                lineBuffer[bufPos++] = c;
        }
    }
}


void parseLine(const char *s)
{
    int newState;
    int newValve;
    float m1, m2, m3, m4, m5;

    int fields = sscanf(
        s,
        "%d,%d,%f,%f,%f,%f,%f",
        &newState,
        &newValve,
        &m1, &m2, &m3, &m4, &m5
    );

    // Must receive exactly 7 values (STATE, VALVESTATE, MFC1, MFC2, MFC3, MFC4, MFC5)
    if (fields != 7)
        return;

    // Valve must be binary
    if (newValve < 0 || newValve > 1)
        return;

    // State change handling
    if (newState != STATE)
    {
        STATE = newState;
        seq = 1;
        if (STATE == 0) // Emergency stop detected, close everything (Probably unessesary to do it here, it should be done by the setpoints coming in as well)
        {
            analogWrite(MFC1_SET_PIN, 0);
            analogWrite(MFC2_SET_PIN, 0);
            analogWrite(MFC3_SET_PIN, 0);
            analogWrite(MFC4_SET_PIN, 0);
            analogWrite(MFC5_SET_PIN, 0);

            digitalWrite(VALVE_SET_PIN, 0);
        }
    }

    VALVE = newValve;
    MFC1 = m1;
    MFC2 = m2;
    MFC3 = m3;
    MFC4 = m4;
    MFC5 = m5;

    applySetpoints();
}

uint16_t mfcToPwm(float slpm)
{
    if (slpm < 0) slpm = 0;
    if (slpm > 500) slpm = 500;
    return (uint16_t)((slpm / 500.0f) * 255.0f);
}

void applySetpoints()
{
    analogWrite(MFC1_SET_PIN, mfcToPwm(MFC1));
    analogWrite(MFC2_SET_PIN, mfcToPwm(MFC2));
    analogWrite(MFC3_SET_PIN, mfcToPwm(MFC3));
    analogWrite(MFC4_SET_PIN, mfcToPwm(MFC4));
    analogWrite(MFC5_SET_PIN, mfcToPwm(MFC5));

    digitalWrite(VALVE_SET_PIN, VALVE ? HIGH : LOW);
}






void sendLine()
{
    readMfcResponses();
    readSensors();


    // Build single line of serial output and send
    outBuffer[0] = '\0';

    char tmp[16];

    strcat(outBuffer, ultoa(seq, tmp, 10));
    strcat(outBuffer, ",");

    strcat(outBuffer, itoa(STATE, tmp, 10));
    strcat(outBuffer, ",");

    strcat(outBuffer, itoa(VALVE, tmp, 10));
    strcat(outBuffer, ",");

    dtostrf(MFC1_RESPONSE, 0, 3, tmp); strcat(outBuffer, tmp); strcat(outBuffer, ",");
    dtostrf(MFC2_RESPONSE, 0, 3, tmp); strcat(outBuffer, tmp); strcat(outBuffer, ",");
    dtostrf(MFC3_RESPONSE, 0, 3, tmp); strcat(outBuffer, tmp); strcat(outBuffer, ",");
    dtostrf(MFC4_RESPONSE, 0, 3, tmp); strcat(outBuffer, tmp); strcat(outBuffer, ",");
    dtostrf(MFC5_RESPONSE, 0, 3, tmp); strcat(outBuffer, tmp); strcat(outBuffer, ",");

    dtostrf(MixingChamberPressure, 0, 3, tmp); strcat(outBuffer, tmp); strcat(outBuffer, ",");
    dtostrf(PipePressure, 0, 3, tmp); strcat(outBuffer, tmp); strcat(outBuffer, ",");
    dtostrf(GasSensor1, 0, 3, tmp); strcat(outBuffer, tmp); strcat(outBuffer, ",");
    dtostrf(GasSensor2, 0, 3, tmp); strcat(outBuffer, tmp);

    strcat(outBuffer, "\n");

    Serial.write(outBuffer);
    seq++;
}


float adcToSlpm(uint16_t adc) // Convert MFC read analog value to SLPM value
{
    if (adc > 1023) adc = 1023;
    return (adc / 1023.0f) * 500.0f;
}
float adcToUnits(uint16_t adc, float fullScale) // read and convert arbitrary sensor pin to arbitrary range
{
    if (adc > 1023) adc = 1023;
    return (adc / 1023.0f) * fullScale;
}

void readMfcResponses()
{
    MFC1_RESPONSE = adcToSlpm(analogRead(MFC1_READ_PIN));
    MFC2_RESPONSE = adcToSlpm(analogRead(MFC2_READ_PIN));
    MFC3_RESPONSE = adcToSlpm(analogRead(MFC3_READ_PIN));
    MFC4_RESPONSE = adcToSlpm(analogRead(MFC4_READ_PIN));
    MFC5_RESPONSE = adcToSlpm(analogRead(MFC5_READ_PIN));
}
void readSensors()
{
    MixingChamberPressure = adcToUnits(analogRead(MixingChamberPressure_PIN),150); // 150 psi full range
    PipePressure = adcToUnits(analogRead(PipePressure_PIN),50); // 50 psi full range
    GasSensor1 = adcToUnits(analogRead(GasSensor1_PIN),1); // UNKOWN FULL RANGE (REQUIRES CALIBRATION)
    GasSensor2 = adcToUnits(analogRead(GasSensor2_PIN),1); // UNKOWN FULL RANGE (REQUIRES CALIBRATION)
}




