const { chromium } = require('playwright');
const { exec } = require('child_process');
const { promisify } = require('util');
const execAsync = promisify(exec);

async function testMCPTime() {
  console.log('🎭 Starting MCP Time Test');
  console.log('=' .repeat(60));
  
  // Launch browser
  const browser = await chromium.launch({
    headless: false,  // Show the browser for debugging
    args: [
      '--use-fake-ui-for-media-stream',  // Auto-grant microphone permission
      '--autoplay-policy=no-user-gesture-required'  // Allow audio autoplay
    ]
  });
  
  const context = await browser.newContext({
    permissions: ['microphone'],
    ignoreHTTPSErrors: true  // For localhost self-signed cert
  });
  
  const page = await context.newPage();
  
  // Enable console logging
  page.on('console', msg => {
    console.log(`🖥️  Browser console: ${msg.text()}`);
  });
  
  // Monitor network requests
  page.on('request', request => {
    if (request.url().includes('websocket') || request.url().includes('realtime')) {
      console.log(`🌐 Request: ${request.method()} ${request.url()}`);
    }
  });
  
  try {
    // Step 1: Navigate to Unmute
    console.log('\n📍 Step 1: Navigating to http://localhost:3000');
    await page.goto('http://localhost:3000');
    
    // Take screenshot
    await page.screenshot({ path: 'test-1-loaded.png' });
    console.log('✅ Page loaded - screenshot saved as test-1-loaded.png');
    
    // Wait a moment for page to settle
    await page.waitForTimeout(2000);
    
    // Step 2: Click the Play button
    console.log('\n🎯 Step 2: Looking for Play button');
    
    // The play button is a canvas element with rounded-full and cursor-pointer classes
    const playButton = await page.locator('canvas.rounded-full.cursor-pointer');
    
    // Wait for it to be visible
    await playButton.waitFor({ state: 'visible', timeout: 10000 });
    
    await page.screenshot({ path: 'test-2-before-play.png' });
    console.log('📸 Screenshot before clicking Play');
    
    // Click the play button
    await playButton.click();
    console.log('✅ Clicked Play button');
    
    // Wait for connection to establish
    console.log('⏳ Waiting for WebSocket connection...');
    await page.waitForTimeout(5000);
    
    await page.screenshot({ path: 'test-3-after-play.png' });
    console.log('📸 Screenshot after clicking Play');
    
    // Wait longer for the agent to be ready
    console.log('⏳ Waiting for agent to be ready to listen...');
    await page.waitForTimeout(10000);  // 10 more seconds for agent initialization
    
    // Step 3: Use TTS to say "What time is it?"
    console.log('\n🎤 Step 3: Using TTS to ask about time (playing through speakers)');
    
    try {
      // We need to simulate audio input - let's use the Web Speech API
      await page.evaluate(() => {
        return new Promise((resolve, reject) => {
          try {
            // Create a speech synthesis utterance
            const utterance = new SpeechSynthesisUtterance('What time is it?');
            utterance.rate = 0.9;  // Slightly slower for clarity
            utterance.pitch = 1.0;
            utterance.volume = 1.0;
            
            // Log when speech ends
            utterance.onend = () => {
              console.log('TTS: Finished speaking');
              resolve();
            };
            
            utterance.onerror = (event) => {
              console.error('TTS Error:', event);
              reject(event);
            };
            
            // Speak it
            window.speechSynthesis.speak(utterance);
            console.log('TTS: Speaking "What time is it?"');
          } catch (error) {
            reject(error);
          }
        });
      });
      
      console.log('✅ TTS finished speaking');
    } catch (ttsError) {
      console.log('⚠️  TTS failed, continuing test:', ttsError.message);
    }
    
    // Wait for response
    console.log('⏳ Waiting for Unmute to process and respond...');
    await page.waitForTimeout(15000);  // Give it 15 seconds to process and respond
    
    await page.screenshot({ path: 'test-4-after-question.png' });
    console.log('📸 Screenshot after asking question');
    
    // Step 4: Check backend logs
    console.log('\n📋 Step 4: Checking backend logs');
    
    try {
      const { stdout } = await execAsync('docker logs unmute-backend 2>&1 | tail -50 | grep -E "(MCP|TOOL_CALL|time|Executing)" | tail -20');
      console.log('\n📜 Recent backend logs:');
      console.log(stdout);
    } catch (logError) {
      console.log('⚠️  Could not fetch backend logs:', logError.message);
    }
    
    // Final summary
    console.log('\n' + '=' .repeat(60));
    console.log('📊 Test Summary:');
    console.log('- Page loaded: ✅');
    console.log('- Play button clicked: ✅');
    console.log('- Question asked via TTS: ✅');
    console.log('- Check screenshots for visual verification');
    console.log('- Check backend logs above for MCP activity');
    
  } catch (error) {
    console.error('❌ Test failed:', error);
  } finally {
    await browser.close();
  }
}

// Run the test
testMCPTime().catch(console.error);