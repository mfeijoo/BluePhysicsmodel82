
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
int dcvch0 = 1800;
int dcvch1 = 2300;
unsigned long previousMillis = 0;
unsigned long previousregMillis = 0;
int resettime = 70;
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
  //digitalWrite (pinpot, LOW);
  //SPI.transfer16( 0x400 | potcount);
  //digitalWrite (pinpot, HIGH);
  SPI.endTransaction();
  regulatePS();
  

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

}

void loop() {


  //Remove dark current
  analogWrite (DAC0, dcvch1); //darkcurrent ch1
  analogWrite (DAC1, dcvch0); //darkcurrent ch0
  

  unsigned long currentMillis = millis();

  if (currentMillis - previousMillis >= integral){

      
      //digitalWrite(pinint, LOW);
      //hold starts
      digitalWrite(A3, HIGH);

      ReadChannels
      
      //Hold ends
      digitalWrite (A3, LOW);


      //As soon as we collect ch0 and ch1
      //we reset the integration and a new integration process starts

      //digitalWrite (pinreset, HIGH);
      digitalWrite (A2, LOW);
      delayMicroseconds (resettime);
      digitalWrite (A2, HIGH);
      previousMillis = millis();
      //digitalWrite (pinint, HIGH);
      //digitalWrite(pinreset, LOW);
      
      

      //while integration is happening
      //we collect the rest of the CDA power values
      //collect the temperature and send everything via serial

      //digitalWrite(pinpowers, HIGH);
      PSc = ads.readADC_SingleEnded(0);
      minus12Vc = ads.readADC_SingleEnded(1);
      cV5 = ads.readADC_SingleEnded(2);
      cV1058 = ads.readADC_SingleEnded(3);
      //digitalWrite(pinpowers, LOW);

      //digitalWrite(pintemp, HIGH);

      //tempsensor.wake();
      temp = tempsensor.readTempC();
      //tempsensor.shutdown_wake(1);

      //digitalWrite(pintemp, LOW);

      //digitalWrite(pinserial, HIGH);
     
      
      //PSV = PSc * 0.1875 / 1000 * 12.914;
      //minus12V = minus12Vc * 0.1875 / 1000 * 2.2;
      //V5 = cV5 * 0.1875 / 1000;
      //V1058 = cV1058 * 0.1875 / 1000 * 2;

      //Include last 10 voltage measurements in an array
      //to calculate average later
      //arrayvolts[i] = PSV;
      //i = i == 9 ? 0 : i + 1;

      //Calculate the average voltage of last 5 measurements
      //sumvolts = 0;
      //for (j = 0; j<10; j++){
        //sumvolts += arrayvolts[j];
     // }

      //avgvolt = sumvolts/10;
      
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

      //digitalWrite(pinserial, LOW);
  }

  /*if (currentMillis - previousregMillis >= regtime){

    //Regulate
      //voltage is too high
      if ((PSV > (setvolt + 0.01)) and (potcount < 1023)){
          potcount = potcount + 1;
          SPI.beginTransaction(SPISettings(50000000, MSBFIRST, SPI_MODE1));
          digitalWrite (pinpot, LOW);
          SPI.transfer16( 0x400 | potcount);
          digitalWrite (pinpot, HIGH);
          SPI.endTransaction();
          }
      //voltage is too low
      else if ((PSV < (setvolt - 0.01)) and (potcount > 0)){
          potcount = potcount - 1;
          SPI.beginTransaction(SPISettings(50000000, MSBFIRST, SPI_MODE1));
          digitalWrite (pinpot, LOW);
          SPI.transfer16( 0x400 | potcount);
          digitalWrite (pinpot, HIGH);
          SPI.endTransaction();
          }

        previousregMillis = millis();
    
  }*/

  if (Serial1.available()>0){

    char inChar = (char)Serial1.read();

    if (inChar == 'r'){
      regulatePS();
    }

    if (inChar == 's'){

      dcvch0 = 1500;
      dcvch1 = 1500;
      analogWrite (DAC0, dcvch1); //darkcurrent ch1
      analogWrite (DAC1, dcvch0); //darkcurrent ch0

      while (voltch0 > 0.05 or
             voltch1 > 0.05){
              if (millis() - previousMillis >= integral){
               ReadChannelsOnce();
               if (voltch0 > 0.05){
                dcvch0 = dcvch0 + 10;
                Serial1.print("dcvch0,");
                Serial1.println(dcvh0);
                analogWrite (DAC1, dcvch0); 
               }
               if (voltch1 > 0.05){
                dcvch1 = dcvch1 + 10;
                Serial1.print("dcvch1,");
                Serial1.println(dcvch1);
                analogWrite (DAC0, dcvch1);
               }
              }
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

      ReadChannels
      
      //Hold ends
      digitalWrite (A3, LOW);


      //As soon as we collect ch0 and ch1
      //we reset the integration and a new integration process starts

      //digitalWrite (pinreset, HIGH);
      digitalWrite (A2, LOW);
      delayMicroseconds (resettime);
      digitalWrite (A2, HIGH);
      previousMillis = millis();
      //digitalWrite (pinint, HIGH);
      //digitalWrite(pinreset, LOW);
}

void regulatePS(){
  //measure PS once
  potlow = 0;
  pothigh = 1023;
  potnow = 512;
  setpot(potnow);
  readPS();
  

  while (PSV > (setvolt + 0.005) or PSV < (setvolt - 0.005)){  
      //voltage is too high
      if (PSV > (setvolt + 0.005)){potlow = potnow;}
      //voltage is too low
      else if (PSV < (setvolt - 0.005)){pothigh = potnow;}
      potnow = int((potlow + pothigh)/2);
      setpot(potnow);
      readPS();
      Serial.print("pothigh: ");
      Serial.println(pothigh);    
      Serial.print("potnow: ");
      Serial.print(potnow);
      Serial.print(", PS: ");
      Serial.println(PSV, 4);
      Serial.print("potlow: ");
      Serial.println(potlow);
      //digitalWrite (13, HIGH);
  }
}

void readPS(){
  PSc = ads.readADC_SingleEnded(0);
  PSV = PSc * 0.1875 / 1000 * 12.914;
}

void setpot(int x){
 SPI.beginTransaction(SPISettings(50000000, MSBFIRST, SPI_MODE1));
 //set the pot
 digitalWrite (pinpot, LOW);
 SPI.transfer16( 0x400 | x);
 digitalWrite (pinpot, HIGH);
 SPI.endTransaction();
 delay(300);
}
