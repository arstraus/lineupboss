/**
 * API URL Format Test
 * 
 * This script tests various URL formats to find the correct API URL
 */
const axios = require('axios');

// Set the token
const token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTc0MjY2MDcyOSwianRpIjoiZTMxNzc3YjUtYjkyOS00M2E5LWIyNTAtNDg4Nzc1ZGU3NDU4IiwidHlwZSI6ImFjY2VzcyIsInN1YiI6IjEiLCJuYmYiOjE3NDI2NjA3MjksImV4cCI6MTc0Mzk1NjcyOX0.x-2T5y0s2Tg1CX1-PM-ildtvIPeDcz4o8WsG24Di8X8';

// URL formats to test
const urlFormats = [
  'https://lineupboss.app/api',
  'https://api.lineupboss.app',
  'https://lineupboss.app',
  'https://www.lineupboss.app/api',
  'http://lineupboss.app/api'
];

// Paths to test
const testPaths = [
  '/teams',
  '/api/teams',
  '/auth/me',
  '/api/auth/me'
];

async function testUrlFormats() {
  console.log('TESTING DIFFERENT API URL FORMATS\n');
  
  for (const baseUrl of urlFormats) {
    console.log(`Testing base URL: ${baseUrl}`);
    
    for (const path of testPaths) {
      try {
        const fullUrl = `${baseUrl}${path}`;
        console.log(`  Trying: ${fullUrl}`);
        
        const response = await axios.get(fullUrl, {
          headers: {
            'Authorization': `Bearer ${token}`
          },
          timeout: 10000
        });
        
        console.log(`  ✅ SUCCESS! Status: ${response.status}`);
        if (Array.isArray(response.data)) {
          console.log(`  Found ${response.data.length} items`);
        } else if (typeof response.data === 'object') {
          console.log(`  Response keys: ${Object.keys(response.data).join(', ')}`);
        }
      } catch (error) {
        if (error.response) {
          console.log(`  ❌ FAILED. Status: ${error.response.status}`);
        } else if (error.request) {
          console.log(`  ❌ FAILED. No response received (timeout or network issue)`);
        } else {
          console.log(`  ❌ FAILED. Error: ${error.message}`);
        }
      }
      console.log('');
    }
    console.log('-'.repeat(50));
  }
}

// Run the test
testUrlFormats();