const puppeteer = require('puppeteer-core');
const os = require('os');
const path = require('path');

async function run() {
  // Use edge or chrome installed on Windows
  const browser = await puppeteer.launch({
    executablePath: 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe',
    headless: true
  });
  const page = await browser.newPage();
  
  page.on('console', msg => console.log('BROWSER LOG:', msg.text()));
  page.on('pageerror', error => console.log('BROWSER ERROR:', error.message));
  
  await page.goto('http://localhost:5173');
  
  // wait for it to load
  await new Promise(r => setTimeout(r, 2000));
  
  // click MONITOR BOOKINGS
  const buttons = await page.$$('button');
  for (let b of buttons) {
    const text = await page.evaluate(el => el.textContent, b);
    if (text.includes('MONITOR BOOKINGS')) {
      await b.click();
      console.log('Clicked MONITOR BOOKINGS');
      break;
    }
  }
  
  await new Promise(r => setTimeout(r, 500));
  
  // click Paste Text
  const buttons2 = await page.$$('button');
  for (let b of buttons2) {
    const text = await page.evaluate(el => el.textContent, b);
    if (text.includes('Paste Text')) {
      await b.click();
      console.log('Clicked Paste Text');
      break;
    }
  }
  
  await new Promise(r => setTimeout(r, 1000));
  await console.log(await page.evaluate(()=>document.body.innerHTML)); await browser.close();
}
run().catch(console.error);
