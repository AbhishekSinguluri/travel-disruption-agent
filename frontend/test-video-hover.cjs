const puppeteer = require('puppeteer-core');
const fs = require('fs');

async function testVideo() {
  const browser = await puppeteer.launch({
    executablePath: 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe',
    headless: true
  });
  const page = await browser.newPage();
  
  try {
    await page.goto('http://localhost:5173');
    await new Promise(r => setTimeout(r, 2000));
    
    console.log("Checking if video is present...");
    const videoExists = await page.evaluate(() => !!document.querySelector('video'));
    console.log("Video present:", videoExists);
    
    if (videoExists) {
      const isPausedInitially = await page.evaluate(() => document.querySelector('video').paused);
      console.log("Video paused initially:", isPausedInitially);
      
      console.log("Hovering over the hero container...");
      const heroBounds = await page.evaluate(() => {
        const h = document.querySelector('.flex.flex-col.md\\:flex-row.gap-16');
        if(!h) return null;
        const rect = h.getBoundingClientRect();
        return { x: rect.x + rect.width / 2, y: rect.y + rect.height / 2 };
      });
      
      if(heroBounds) {
        await page.mouse.move(heroBounds.x, heroBounds.y);
        await new Promise(r => setTimeout(r, 1000));
        
        const isPausedAfterHover = await page.evaluate(() => document.querySelector('video').paused);
        console.log("Video paused after hover in:", isPausedAfterHover);
        
        console.log("Hovering outside the hero container...");
        await page.mouse.move(0, 0);
        await new Promise(r => setTimeout(r, 1000));
        
        const isPausedAfterHoverOut = await page.evaluate(() => document.querySelector('video').paused);
        console.log("Video paused after hover out:", isPausedAfterHoverOut);
      } else {
        console.log("Hero container not found!");
      }
    }
    
  } catch (err) {
    console.error(err);
  } finally {
    await browser.close();
  }
}

testVideo();
