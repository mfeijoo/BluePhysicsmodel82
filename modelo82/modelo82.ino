
#include <SPI.h>
#include <Wire.h>
#include "Adafruit_MCP9808.h"
#include <Adafruit_ADS1015.h>

Adafruit_MCP9808 tempsensor = Adafruit_MCP9808();
Adafruit_ADS1115 ads;


int resultch0;
int resultch1;
int16_t PSc;
int16_t minus12Vc;
int16_t cV5;
int16_t cV1058;
float voltch0;
float voltch1;
float PSV;
float minus12V;
float V5;
float V1058;
int integral = 150;
int regtime = 233;
unsigned long previousMillis = 0;
unsigned long previousregMillis = 0;
int resettime = 500;
int pinpot = 2;
int potcount; //pot value in counts from 0 to 1023
float setvolt = 56;
//unsigned char i=0;
//unsigned char j;
//float arrayvolts[]={57.128, 57.128, 57.128, 57.128, 57.128, 57.128, 57.128, 57.128, 57.128, 57.128};
//float sumvolts = 0.0000;
//float avgvolt = 0.0000;
float temp = 27;
//int pinint = 7;
//int pintemp = 10;
//int pinserial = 11;
//int pinpowers = 12;
//int pinreset = 13;
unsigned int dcvch0 = 32767;
unsigned int dcvch1 = 32767;
unsigned int dcvch0max = 65535;
unsigned int dcvch1max = 65535;
unsigned int dcvch0min = 0;
unsigned int dcvch1min = 0;

void setup() {


  analogWriteResolution(12); //4095

  
  Serial1.begin (115200);

  //RESET
  pinMode (A2, OUTPUT);
  digitalWrite (A2, HIGH);
  //HOLD
  pinMode (A3, OUTPUT);
  digitalWrite (A3, LOW);
  //ADC0
  pinMode (A4, OUTPUT);
  digitalWrite (A4, HIGH);
  //ADC1
  pinMode (A5, OUTPUT);
  digitalWrite (A5, HIGH);
  //POT
  pinMode (pinpot, OUTPUT);
  digitalWrite (pinpot, HIGH);

  /*pinMode (pinint, OUTPUT);
  digitalWrite(pinint, HIGH);
  pinMode (pintemp, OUTPUT);
  digitalWrite (pintemp, LOW);
  pinMode (pinserial, OUTPUT);
  digitalWrite (pinserial, LOW);
  pinMode (pinpowers, OUTPUT);
  digitalWrite (pinpowers, LOW);
  pinMode (pinreset, OUTPUT);
  digitalWrite (pinreset, LOW);*/
  


  SPI.begin();
  
  ads.setGain(GAIN_TWOTHIRDS); // 2/3X GAIN +/- 6.144v 1BI = 3mV (default)
  ads.begin();
  
  
  tempsensor.begin(0x18);
  tempsensor.setResolution(3);
  // Mode Resolution SampleTime
  //  0    0.5°C       30 ms
  //  1    0.25°C      65 ms
  //  2    0.125°C     130 ms
  //  3    0.0625°C    250 ms
  tempsensor.wake();
  

  potcount = (int)(((4253.16/(setvolt - 10.58)) - 84.5)*102.3);
  //potcount = 1023;
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
  

  SPI.beginTransaction(SPISettings(66670000, MSBFIRST, SPI_MODE0));
  digitalWrite (A4, LOW);
  SPI.transfer16 (0b1101000000010100);
  SPI.transfer16 (0b0000000000000000);
  digitalWrite (A4, HIGH);
  
  digitalWrite (A5, LOW);
  SPI.transfer16 (0b1101000000010100);
  SPI.transfer16 (0b0000000000000000);
  digitalWrite (A5, HIGH);
  SPI.endTransaction();

  //Remove dark current
  analogWrite (DAC0, dcvch1); //darkcurrent ch1
  analogWrite (DAC1, dcvch0); //darkcurrent ch0

}

void loop() {


  //Remove dark current
  //analogWrite (DAC0, 2300); //darkcurrent ch1
  //analogWrite (DAC1, 1800); //darkcurrent ch0
  

  unsigned long currentMillis = millis();

  if (currentMillis - previousMillis >= integral){
   
   ReadChannelsOnce();
   
   //while integration is happening
   //we collect the rest of the CDA power values
   //collect the temperature and send everything via serial
   PSc = ads.readADC_SingleEnded(0);
   minus12Vc = ads.readADC_SingleEnded(1);
   cV5 = ads.readADC_SingleEnded(2);
   cV1058 = ads.readADC_SingleEnded(3);
   
   temp = tempsensor.readTempC();
   

   //PSV = PSc * 0.1875 / 1000 * 12.914;
   //minus12V = minus12Vc * 0.1875 / 1000 * 2.2;
   //V5 = cV5 * 0.1875 / 1000;
   //V1058 = cV1058 * 0.1875 / 1000 * 2;
   
   Serial1.print(previousMillis);
   Serial1.print(",");
   Serial1.print(temp, 4);
   Serial1.print(",");
   Serial1.print(resultch0);
   Serial1.print(",");
   Serial1.print(resultch1);
   Serial1.print(",");
   Serial1.print(PSc);
   Serial1.print(",");
   Serial1.print(minus12Vc);
   Serial1.print(",");
   Serial1.print(cV5);
   Serial1.print(",");
   Serial1.println(cV1058);
 }


 if (Serial1.available() > 0){
  char inChar = (char)Serial1.read();
  
  if (inChar == 'c'){
   String intts = Serial1.readStringUntil(',');
   char pulsint = (char)Serial1.read();
   //Serial.println(intts.toInt());
   //Serial.println(pulsint);
   integral = intts.toInt();
   if (pulsint == 'I') {
    //HIGH for integrator
    digitalWrite (A4, HIGH);
    }
   if (pulsint == 'P'){
    //LOW for pulses
    digitalWrite (A4, LOW);
   }
  }
 }
}

void ReadChannels(){
 
 SPI.beginTransaction(SPISettings(66670000, MSBFIRST, SPI_MODE0));
 
 digitalWrite (A4, LOW);
 resultch0 = SPI.transfer16 (0b1101000000010000);
 SPI.transfer16 (0b0000000000000000);
 digitalWrite (A4, HIGH);
  
 digitalWrite (A5, LOW);
 resultch1 = SPI.transfer16 (0b1101000000010000);
 SPI.transfer16 (0b0000000000000000);
 digitalWrite (A5, HIGH);
 
 SPI.endTransaction();

 //voltch0 = -resultch0 * 0.000375 + 12.288;
 //voltch1 = -resultch1 * 0.000375 + 12.288;
}

void ReadChannelsOnce(){
 
 //digitalWrite(pinint, LOW);
 
 //hold starts
 digitalWrite(A3, HIGH);
 ReadChannels();
 //Hold ends
 digitalWrite (A3, LOW);
 
 //As soon as we collect ch0 and ch1
 //we reset the integration and a new integration process starts
 digitalWrite (A2, LOW);
 delayMicroseconds (resettime);
 digitalWrite (A2, HIGH);
 previousMillis = millis();
}

//function to subtract dark current
void sdc(){
 dcvch0 = 32767;
 dcvch1 = 32767;
 dcvch0max = 65535;
 dcvch1max = 65535;
 dcvch0min = 0;
 dcvch1min = 0;
 analogWrite (DAC1, dcvch0);
 analogWrite (DAC0, dcvch1);
 while (millis() - previousMillis < integral){
 }
 ReadChannelsOnce();
 Serial.print("dcvch0min:");
 Serial.print(dcvch0min);
 Serial.print("dcvch0:");
 Serial.print(dcvch0);
 Serial.print("dcvch0max:");
 Serial.print(dcvch0max);
 Serial.print("voltch0:");
 Serial.println(voltch0);
 Serial.print("dcvch1min:");
 Serial.print(dcvch1min);
 Serial.print("dcvch1:");
 Serial.print(dcvch1);
 Serial.print("dcvch1max:");
 Serial.print(dcvch1max);
 Serial.print("voltch1:");
 Serial.println(voltch1);
 while (millis() - previousMillis < integral){
 }
 ReadChannelsOnce();
 while (resultch0 < 32742 or resultch0 > 32792){
  if (resultch0 < 32742){
    dcvh0min = dcvch0;
  }
  if (resultch0 > 32792){
    dcvh0max = cdvch0;
  }
  dcvch0 = int((dcvch0min + dcvch0max)/2);
  analogWrite(DAC1, dcvch0);
  while (millis() - previousMillis < integral){
  }
  ReadChannelsOnce();
  Serial.print("dcvch0min:");
  Serial.print(dcvch0min);
  Serial.print("dcvch0:");
  Serial.print(dcvch0);
  Serial.print("dcvch0max:");
  Serial.print(dcvch0max);
  Serial.print("voltch0:");
  Serial.println(resultch0);
 }
 while (resultch1 < 32742 or resultch1 > 32792){
  if (resultch1 < 32742){
    dcvh1min = dcvch1;
  }
  if (resultch1 > 32792){
    dcvh1max = cdvch1;
  }
  dcvch1 = int((dcvch1min + dcvch1max)/2);
  analogWrite(DAC0, dcvch1);
  while (millis() - previousMillis < integral){
  }
  ReadChannelsOnce();
  Serial.print("dcvch1min:");
  Serial.print(dcvch1min);
  Serial.print("dcvch1:");
  Serial.print(dcvch1);
  Serial.print("dcvch1max:");
  Serial.print(dcvch1max);
  Serial.print("ch1count:");
  Serial.println(resultch1);
 }
}
 

