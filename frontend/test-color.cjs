const puppeteer = require('puppeteer-core');
const fs = require('fs');
const http = require('http');

async function run() {
  const browser = await puppeteer.launch({
    executablePath: 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe',
    headless: true
  });
  const page = await browser.newPage();
  await page.setViewport({ width: 1200, height: 800 });
  await page.goto('http://localhost:5173');
  await new Promise(r => setTimeout(r, 2000));
  
  // Get color at (10, 10) which is definitely outside the video
  // Get color at (200, 400) which should be inside the left side of the video boundary
  
  const colors = await page.evaluate(async () => {
    return new Promise(resolve => {
       // We can capture the screen but easier is to render dom to canvas or just take a screenshot and pass it to node
       resolve(true);
    });
  });
  
  await page.screenshot({ path: 'screenshot.png' });
  await browser.close();
}

run();
