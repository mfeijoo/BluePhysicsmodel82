
#include <SPI.h>
#include <Wire.h>
#include "Adafruit_MCP9808.h"

Adafruit_MCP9808 tempsensor = Adafruit_MCP9808();

int pinCS = 7; 
int resultch0;
int resultch1;
int resultch2;
int resultch3;
int resultch4;
int resultch5;
int resultch6;
int resultch7;
float voltch0;
float voltch1;
float voltch2;
float voltch3;
float voltch4;
float voltch5;
float voltch6;
float voltch7;
int integral = 120;
unsigned long previousMillis = 0;
int resettime = 500;
int pinpot = 9;
int potcount; //pot value in counts from 0 to 1023
float setvolt = 57;
unsigned char i;
unsigned char j;
float arrayvolts[]={57, 57, 57, 57, 57, 57, 57, 57, 57, 57, 57, 57, 57, 57, 57, 57, 57, 57, 57, 57};
float sumvolts = 0.0000;
float avgvolt = 0.0000;
float temp = 27;
int pintest = 11;

void setup() {


  analogWriteResolution(12); //4096

  
  Serial1.begin (115200);

  pinMode (pinCS, OUTPUT);
  pinMode (A3, OUTPUT);
  digitalWrite (pinCS, HIGH);
  digitalWrite (A3, HIGH);
  //hold pin
  pinMode (A4, OUTPUT);
  digitalWrite(A4, LOW);
  pinMode (pinpot, OUTPUT);
  digitalWrite(pinpot, HIGH);

  pinMode (pintest, OUTPUT);
  digitalWrite(pintest, LOW);

  SPI.begin();
  tempsensor.begin(0x18);
  tempsensor.setResolution(3);
  // Mode Resolution SampleTime
  //  0    0.5°C       30 ms
  //  1    0.25°C      65 ms
  //  2    0.125°C     130 ms
  //  3    0.0625°C    250 ms
  tempsensor.wake();
  

  potcount = (int)(((4253.16/(setvolt - 10.58)) - 84.5)*102.3);
  SPI.beginTransaction(SPISettings(50000000, MSBFIRST, SPI_MODE1));
  //Remove protection from the potentiometer
  digitalWrite(pinpot, LOW);
  SPI.transfer16(0x1c03);
  digitalWrite(pinpot, HIGH);
  //set the pot for the first time
  digitalWrite (pinpot, LOW);
  SPI.transfer16( 0x400 | potcount);
  digitalWrite (pinpot, HIGH);
  SPI.endTransaction();
  

  SPI.beginTransaction(SPISettings(17000000, MSBFIRST, SPI_MODE1));

  //Set Range for ch0
  //ch0 0b0000101 (0x05)
  //write 0b1
  //Range select first 0b0000
  //Range select final -2.25 to +2.25 x Vref(4.096V) 0b0000
  //Then we have to send a dummy byte 0b00000000
  //It means hex(0b0000101100000000) = 0xb00 as a 16bit
  //then the dummy byte of 0b00000000
  digitalWrite (pinCS, LOW);
  SPI.transfer16 (0xb00);
  SPI.transfer (0x00);
  digitalWrite (pinCS, HIGH);
  
  //Set Range for ch1
  //ch1 0b0000110
  //write 0b1
  //Range select first 0b0000
  //Range select final -2.25 to +2.25 x Vref(4.096V) 0b0000
  //Then we have to send a dummy byte 0b00000000
  //It means hex(0b0000110100000000) = 0xd00 as a 16bit
  //then the dummy byte of 0b00000000
  digitalWrite (pinCS, LOW);
  SPI.transfer16 (0xd00);
  SPI.transfer (0x00);
  digitalWrite (pinCS, HIGH);

  //Set Range for ch2
  //ch3 0b0000111
  //write 0b1
  //Range select first 0b0000
  //Range select final -2.25 to +2.25 x Vref(4.096V) 0b0000
  //Then we have to send a dummy byte 0b00000000
  //It means hex(0b0000111100000000) = 0xf00 as a 16bit
  //then the dummy byte of 0b00000000
  digitalWrite (pinCS, LOW);
  SPI.transfer16 (0xf00);
  SPI.transfer (0x00);
  digitalWrite (pinCS, HIGH);
  
  //Set Range for ch3
  //ch3 0b0001000
  //write 0b1
  //Range select first 0b0000
  //Range select final -2.25 to +2.25 x Vref(4.096V) 0b0000
  //Then we have to send a dummy byte 0b00000000
  //It means hex(0b0001000100000000) = 0x1100 as a 16bit
  //then the dummy byte of 0b00000000
  digitalWrite (pinCS, LOW);
  SPI.transfer16 (0x1100);
  SPI.transfer (0x00);
  digitalWrite (pinCS, HIGH);

  //Set Range for ch4
  //ch4 0b0001001
  //write 0b1
  //Range select first 0b0000
  //Range select final -2.25 to +2.25 x Vref(4.096V) 0b0000
  //Then we have to send a dummy byte 0b00000000
  //It means hex(0b0001001100000000) = 0x1300 as a 16bit
  //then the dummy byte of 0b00000000
  digitalWrite (pinCS, LOW);
  SPI.transfer16 (0x1300);
  SPI.transfer (0x00);
  digitalWrite (pinCS, HIGH);

  //Set Range for ch5
  //ch5 0b0001010
  //write 0b1
  //Range select first 0b0000
  //Range select final -2.25 to +2.25 x Vref(4.096V) 0b0000
  //Then we have to send a dummy byte 0b00000000
  //It means hex(0b0001010100000000) = 0x1500 as a 16bit
  //then the dummy byte of 0b00000000
  digitalWrite (pinCS, LOW);
  SPI.transfer16 (0x1500);
  SPI.transfer (0x00);
  digitalWrite (pinCS, HIGH);

  //Set Range for ch6
  //ch6 0b0001011
  //write 0b1
  //Range select first 0b0000
  //Range select final -2.25 to +2.25 x Vref(4.096V) 0b0000
  //Then we have to send a dummy byte 0b00000000
  //It means hex(0b0001011100000000) = 0x1700 as a 16bit
  //then the dummy byte of 0b00000000
  digitalWrite (pinCS, LOW);
  SPI.transfer16 (0x1700);
  SPI.transfer (0x00);
  digitalWrite (pinCS, HIGH);

  //Set Range for ch7
  //ch7 0b0001100
  //write 0b1
  //Range select first 0b0000
  //Range select final -2.25 to +2.25 x Vref(4.096V) 0b0000
  //Then we have to send a dummy byte 0b00000000
  //It means hex(0b0001100100000000) = 0x1900 as a 16bit
  //then the dummy byte of 0b00000000
  digitalWrite (pinCS, LOW);
  SPI.transfer16 (0x1900);
  SPI.transfer (0x00);
  digitalWrite (pinCS, HIGH);

  SPI.endTransaction();


}

void loop() {

  //Remove dark current
  analogWrite (DAC0, 3800);
  analogWrite (DAC1, 3500);
  

  unsigned long currentMillis = millis();

  if (currentMillis - previousMillis >= integral){

      digitalWrite(pintest, HIGH);
      //hold starts
      digitalWrite(A4, HIGH);
  
      SPI.beginTransaction(SPISettings(17000000, MSBFIRST, SPI_MODE1));

      //start Manual ch1 collection
      //and read previous selection (ch0)
      //first send 0xc400 
      //Ch1 input is selected
      //then send  0b0000000000000000 and read previous measuerment at ch0
      digitalWrite (pinCS, LOW);
      SPI.transfer16(0xc400);
      resultch0 = SPI.transfer16(0x0000);
      digitalWrite(pinCS, HIGH);

      //start Manual ch2 collection
      //and read previous selection (ch1)
      //first send 0xc800 
      //Ch1 input is selected
      //then send  0b0000000000000000 and read previous measuerment at ch0
      digitalWrite (pinCS, LOW);
      SPI.transfer16(0xc800);
      resultch1 = SPI.transfer16(0x0000);
      digitalWrite(pinCS, HIGH);

      SPI.endTransaction();

      //Hold ends
      digitalWrite (A4, LOW);
      digitalWrite (pintest, LOW);

      //As soon as we collect ch0 and ch1
      //we reset the integration and a new integration process starts


      digitalWrite (A3, LOW);
      delayMicroseconds (resettime);
      digitalWrite (A3, HIGH);
      previousMillis = millis();
      digitalWrite (pintest, HIGH);
      
      

      //while integration is happening
      //we collect the rest of the CDA power values
      //collect the temperature and send everything via serial

      SPI.beginTransaction(SPISettings(17000000, MSBFIRST, SPI_MODE1));
  
      //start Manual ch3 collection
      //and read previous selection (ch2)
      //first send 0xcc00 
      //Ch1 input is selected
      //then send  0b0000000000000000 and read previous measuerment at ch0
      digitalWrite (pinCS, LOW);
      SPI.transfer16(0xcc00);
      resultch2 = SPI.transfer16(0x0000);
      digitalWrite(pinCS, HIGH);

      //start Manual ch4 collection
      //and read previous selection (ch3)
      //first send 0xd000 
      //Ch1 input is selected
      //then send  0b0000000000000000 and read previous measuerment at ch0
      digitalWrite (pinCS, LOW);
      SPI.transfer16(0xd000);
      resultch3 = SPI.transfer16(0x0000);
      digitalWrite(pinCS, HIGH);

      //start Manual ch5 collection
      //and read previous selection (ch4)
      //first send 0xd400 
      //Ch1 input is selected
      //then send  0b0000000000000000 and read previous measuerment at ch0
      digitalWrite (pinCS, LOW);
      SPI.transfer16(0xd400);
      resultch4 = SPI.transfer16(0x0000);
      digitalWrite(pinCS, HIGH);

      //start Manual ch6 collection
      //and read previous selection (ch5)
      //first send 0xd800 
      //Ch1 input is selected
      //then send  0b0000000000000000 and read previous measuerment at ch0
      digitalWrite (pinCS, LOW);
      SPI.transfer16(0xd800);
      resultch5 = SPI.transfer16(0x0000);
      digitalWrite(pinCS, HIGH);

      //start Manual ch7 collection
      //and read previous selection (ch6)
      //first send 0xdc00 
      //Ch1 input is selected
      //then send  0b0000000000000000 and read previous measuerment at ch0
      digitalWrite (pinCS, LOW);
      SPI.transfer16(0xdc00);
      resultch6 = SPI.transfer16(0x0000);
      digitalWrite(pinCS, HIGH);

      //start Manual ch0 collection
      //and read previous selection (ch7)
      //first send 0xc000 
      //Ch0 input is selected
      //then send  0b0000000000000000 and read previous measuerment at ch1
      digitalWrite (pinCS, LOW);
      SPI.transfer16 (0xc000); 
      resultch7 = SPI.transfer16 (0x0000);
      digitalWrite (pinCS, HIGH);

     SPI.endTransaction();

     digitalWrite(pintest, LOW);

     temp = tempsensor.readTempC();
    
     digitalWrite(pintest, HIGH);
     
      voltch0 = -resultch0 * 0.0003125 + 10.24;
      voltch1 = -resultch1 * 0.0003125 + 10.24;
      voltch2 = resultch2 * 0.0003125 - 10.24;
      voltch3 = (resultch3 * 0.0003125 - 10.24) * 2.2;
      voltch4 = (resultch4 * 0.0003125 - 10.24) * 2.2;
      voltch5 = (resultch5 * 0.0003125 - 10.24) * 2.2;
      voltch6 = (resultch6 * 0.0003125 - 10.24) * 6.6;
      voltch7 = (resultch7 * 0.0003125 - 10.24) * 9.6;

      //Include last 20 voltage measurements in an array
      //to calculate average later
      arrayvolts[i] = voltch6;
      i = i == 19 ? 0 : i + 1;

      //Calculate the average voltage of last 5 measurements
      sumvolts = 0;
      for (j = 0; j<20; j++){
        sumvolts += arrayvolts[j];
      }

      avgvolt = sumvolts/20;
      
      Serial1.print(previousMillis);
      Serial1.print(",");
      Serial1.print(temp, 4);
      Serial1.print(",");
      Serial1.print(voltch0, 4);
      Serial1.print(",");
      Serial1.print(voltch1, 4);
      Serial1.print(",");
      Serial1.print(voltch2, 4);
      Serial1.print(",");
      Serial1.print(voltch3, 4);
      Serial1.print(",");
      Serial1.print(voltch4, 4);
      Serial1.print(",");
      Serial1.print(voltch5, 4);
      Serial1.print(",");
      Serial1.print(voltch6, 4);
      Serial1.print(",");
      Serial1.println(voltch7, 4);

      digitalWrite (pintest, LOW);

      /*//Regulate
      //voltage is too high
      if (avgvolt > (setvolt + 0.01)){
          potcount = potcount + 1;
          SPI.beginTransaction(SPISettings(50000000, MSBFIRST, SPI_MODE1));
          digitalWrite (pinpot, LOW);
          SPI.transfer16( 0x400 | potcount);
          digitalWrite (pinpot, HIGH);
          SPI.endTransaction();
          }
      //voltage is too low
      else if (avgvolt < (setvolt - 0.03)){
          potcount = potcount - 1;
          SPI.beginTransaction(SPISettings(50000000, MSBFIRST, SPI_MODE1));
          digitalWrite (pinpot, LOW);
          SPI.transfer16( 0x400 | potcount);
          digitalWrite (pinpot, HIGH);
          SPI.endTransaction();
          }*/
  }
}
