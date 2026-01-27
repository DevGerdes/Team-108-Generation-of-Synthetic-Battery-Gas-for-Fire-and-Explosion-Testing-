#include <stdlib.h>

const uint32_t BAUD = 93000;

#define MAX_MFC 5 // Max number of MFC's (Shouldn't increase)
#define MAX_SENSORS 8 // Max number of sensors (can be increased)(MFC response read, gas sniffers, pressure etc.)
#define OUTBUF_SIZE 160 // Max charecter length for serial out. Makes things truncate safely for sending if too long, and can be increased if needed (shouldnt need to)

float STATE = 0; // Default to emergency stop to close everything down
float VALVE = 0; // Default closed
float MFC_RATES[MAX_MFC];
uint8_t MFC_COUNT = 0;

float sensorValues[MAX_SENSORS];
uint8_t SENSOR_COUNT = 3;   // number of sensors

char lineBuffer[96];
uint8_t bufPos = 0;

char outBuffer[OUTBUF_SIZE]; // the actual buffered output message

uint32_t seq = 1;
float lastState = 0;

void setup()
{
    Serial.begin(BAUD);
}

void loop()
{
    while (Serial.available())
    {
        char c = Serial.read();

        if (c == '\n')
        {
            lineBuffer[bufPos] = 0;
            parseLine(lineBuffer);
            sendLine();
            bufPos = 0;
        }
        else if (c != '\r')
        {
            if (bufPos < sizeof(lineBuffer) - 1)
                lineBuffer[bufPos++] = c;
        }
    }

    // Example sensors
    sensorValues[0] = analogRead(A0);
    sensorValues[1] = analogRead(A1);
    sensorValues[2] = millis() * 0.001;
}

void parseLine(char *s)
{
    char *tok = strtok(s, ",");

    if (!tok) return;
    float newState = atof(tok);

    tok = strtok(NULL, ",");
    if (!tok) return;
    VALVE = atof(tok);

    if (newState != STATE)
    {
        STATE = newState;
        seq = 1;          // reset sequence on state change
    }
    else
    {
        STATE = newState;
    }

    MFC_COUNT = 0;
    while ((tok = strtok(NULL, ",")) && MFC_COUNT < MAX_MFC)
    {
        MFC_RATES[MFC_COUNT++] = atof(tok);
    }
}

void sendLine()
{
  // Combine the whole message into one buffered output
  // Sent lines begin with an increasing number designation to prevent repeated line reading at main computer
  // Inspired by SCADA protocol
    outBuffer[0] = 0;   // hard reset the string to avoid ghost fields
    int n = 0; // number of charecters in message

    // write first 3 items into buffer
    n += snprintf(outBuffer + n, OUTBUF_SIZE - n, "%lu,%.3f,%.3f",
                  seq, STATE, VALVE);

    // write the MFC values into the buffer
    for (uint8_t i = 0; i < MFC_COUNT; i++)
        n += snprintf(outBuffer + n, OUTBUF_SIZE - n, ",%.3f", MFC_RATES[i]);

    // write the sensor values into the buffer
    for (uint8_t i = 0; i < SENSOR_COUNT; i++)
        n += snprintf(outBuffer + n, OUTBUF_SIZE - n, ",%.3f", sensorValues[i]);

    // Send data to serial
    Serial.println(outBuffer);   // ONE transmit

    // increment sent data sequence value
    seq++;
}




